from pathlib import Path

ROOT = Path.cwd()
PUBSPEC = ROOT / 'pubspec.yaml'
GALLERY = ROOT / 'lib' / 'src' / 'gallery_page.dart'
MANIFEST = ROOT / 'android' / 'app' / 'src' / 'main' / 'AndroidManifest.xml'

NEW_GALLERY_PAGE = r"""
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:gallery_saver_plus/gallery_saver.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'i18n.dart';
import 'models.dart';
import 'pixel_widgets.dart';
import 'helpers.dart';

class GalleryPage extends StatefulWidget {
  const GalleryPage({super.key, required this.controller});
  final AppController controller;

  @override
  State<GalleryPage> createState() => _GalleryPageState();
}

class _GalleryPageState extends State<GalleryPage> {
  final Set<String> _savingQuestIds = <String>{};
  bool _savingAll = false;

  bool get _busy => _savingAll || _savingQuestIds.isNotEmpty;

  @override
  Widget build(BuildContext context) {
    final l = L10n(widget.controller.settings.language);
    final c = appColors(context);
    final quests = widget.controller.completedQuests().where((q) => q.photoPaths.isNotEmpty).toList();

    return Scaffold(
      backgroundColor: Colors.transparent,
      body: ListView(
        padding: const EdgeInsets.fromLTRB(22, 18, 22, 120),
        children: <Widget>[
          SectionTitle(l.gallery),
          Text(
            'For LMS upload: save the quest images to your phone gallery first, then open LMS, press Choose File, and pick Photos & videos.',
            style: TextStyle(color: c.muted, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 14),
          if (quests.isNotEmpty)
            PixelButton(
              label: _savingAll ? 'SAVING...' : 'SAVE ALL TO PHONE GALLERY',
              filled: true,
              onPressed: _busy ? null : () => _saveAllToGallery(quests),
            ),
          const SizedBox(height: 16),
          if (quests.isEmpty)
            Center(child: Padding(padding: const EdgeInsets.all(40), child: Text(l.noQuest)))
          else
            for (final q in quests) _QuestGalleryCard(
              quest: q,
              saving: _savingQuestIds.contains(q.id),
              onSave: _busy ? null : () => _saveQuestToGallery(q),
              onOpenLms: q.lmsUrl.isEmpty ? null : () => openExternalLink(context, q.lmsUrl),
            ),
        ],
      ),
    );
  }

  Future<void> _saveAllToGallery(List<Quest> quests) async {
    if (_busy) return;
    setState(() => _savingAll = true);
    var saved = 0;
    var total = 0;
    try {
      for (final q in quests) {
        final result = await _savePaths(q.photoPaths);
        saved += result.saved;
        total += result.total;
      }
      if (!mounted) return;
      _showResult(saved, total);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Could not save images: $e')));
    } finally {
      if (mounted) setState(() => _savingAll = false);
    }
  }

  Future<void> _saveQuestToGallery(Quest quest) async {
    if (_busy) return;
    setState(() => _savingQuestIds.add(quest.id));
    try {
      final result = await _savePaths(quest.photoPaths);
      if (!mounted) return;
      _showResult(result.saved, result.total);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Could not save images: $e')));
    } finally {
      if (mounted) setState(() => _savingQuestIds.remove(quest.id));
    }
  }

  Future<_GallerySaveResult> _savePaths(List<String> paths) async {
    var saved = 0;
    var total = 0;

    for (final path in paths.take(10)) {
      final file = File(path);
      if (!await file.exists()) continue;
      total += 1;
      final ok = await GallerySaver.saveImage(file.path);
      if (ok == true) saved += 1;
    }

    return _GallerySaveResult(saved: saved, total: total);
  }

  void _showResult(int saved, int total) {
    final message = total == 0
        ? 'No existing image file was found.'
        : 'Saved $saved/$total images. Now open LMS > Choose File > Photos & videos.';
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }
}

class _GallerySaveResult {
  const _GallerySaveResult({required this.saved, required this.total});
  final int saved;
  final int total;
}

class _QuestGalleryCard extends StatelessWidget {
  const _QuestGalleryCard({
    required this.quest,
    required this.saving,
    required this.onSave,
    required this.onOpenLms,
  });

  final Quest quest;
  final bool saving;
  final VoidCallback? onSave;
  final VoidCallback? onOpenLms;

  @override
  Widget build(BuildContext context) {
    final c = appColors(context);
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: c.panel.withValues(alpha: 0.85),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: c.line.withValues(alpha: 0.55), width: 2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            quest.title.toUpperCase(),
            style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w900, letterSpacing: 2),
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: <Widget>[
              for (final p in quest.photoPaths)
                ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: Image.file(
                    File(p),
                    width: 92,
                    height: 92,
                    fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => Container(
                      width: 92,
                      height: 92,
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: c.line, width: 2),
                      ),
                      child: const Icon(Icons.broken_image),
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: <Widget>[
              Expanded(
                child: PixelButton(
                  label: saving ? 'SAVING...' : 'SAVE TO GALLERY',
                  filled: true,
                  onPressed: onSave,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: PixelButton(
                  label: 'OPEN LMS',
                  filled: false,
                  onPressed: onOpenLms,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

""".strip() + "\n"

def backup(path: Path, suffix: str = '.bak_v7') -> None:
    if path.exists():
        b = path.with_suffix(path.suffix + suffix)
        if not b.exists():
            b.write_text(path.read_text(encoding='utf-8'), encoding='utf-8')

def ensure_dependency() -> None:
    if not PUBSPEC.exists():
        raise SystemExit('pubspec.yaml not found. Run this script from the Flutter project root.')
    text = PUBSPEC.read_text(encoding='utf-8')
    if 'gallery_saver_plus:' in text:
        return
    lines = text.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if not inserted and line.strip().startswith('shared_preferences:'):
            indent = line[:len(line) - len(line.lstrip())]
            out.append(f'{indent}gallery_saver_plus: 3.2.9')
            inserted = True
    if not inserted:
        # fallback: add under dependencies
        out = []
        for line in lines:
            out.append(line)
            if line.strip() == 'dependencies:':
                out.append('  gallery_saver_plus: 3.2.9')
                inserted = True
    PUBSPEC.write_text('\n'.join(out) + '\n', encoding='utf-8')

def patch_gallery_page() -> None:
    if not GALLERY.exists():
        raise SystemExit(f'{GALLERY} not found.')
    backup(GALLERY)
    GALLERY.write_text(NEW_GALLERY_PAGE, encoding='utf-8')

def patch_android_manifest() -> None:
    if not MANIFEST.exists():
        return
    text = MANIFEST.read_text(encoding='utf-8')
    changed = False
    permission = '<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="29" />'
    if 'android.permission.WRITE_EXTERNAL_STORAGE' not in text:
        text = text.replace('<application', f'    {permission}\n\n    <application', 1)
        changed = True
    if changed:
        backup(MANIFEST)
        MANIFEST.write_text(text, encoding='utf-8')

def main() -> None:
    ensure_dependency()
    patch_gallery_page()
    patch_android_manifest()
    print('PIXDO v7 LMS gallery export patch applied.')
    print('Next: flutter clean && flutter pub get && flutter run')
    print('Usage: PIXDO Gallery page -> SAVE TO GALLERY -> LMS Choose File -> Photos & videos.')

if __name__ == '__main__':
    main()
