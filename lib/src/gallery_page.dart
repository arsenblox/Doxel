
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:gallery_saver_plus/gallery_saver.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'helpers.dart';
import 'i18n.dart';
import 'models.dart';
import 'pixel_widgets.dart';

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
            style: TextStyle(color: c.muted, fontWeight: FontWeight.w900, height: 1.2),
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
          const SizedBox(height: 8),
          Text('Tap image to preview', style: TextStyle(color: c.muted, fontSize: 12, fontWeight: FontWeight.w900)),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: <Widget>[
              for (int i = 0; i < quest.photoPaths.length; i++)
                InkWell(
                  borderRadius: BorderRadius.circular(12),
                  onTap: () => showGalleryImagePreview(context, quest.photoPaths, i),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(12),
                    child: Image.file(
                      File(quest.photoPaths[i]),
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

Future<void> showGalleryImagePreview(BuildContext context, List<String> paths, int initialIndex) async {
  if (paths.isEmpty) return;
  final safeInitial = initialIndex.clamp(0, paths.length - 1).toInt();
  await showDialog<void>(
    context: context,
    barrierColor: Colors.black87,
    builder: (_) => _GalleryImagePreviewDialog(paths: List<String>.from(paths), initialIndex: safeInitial),
  );
}

class _GalleryImagePreviewDialog extends StatefulWidget {
  const _GalleryImagePreviewDialog({required this.paths, required this.initialIndex});
  final List<String> paths;
  final int initialIndex;

  @override
  State<_GalleryImagePreviewDialog> createState() => _GalleryImagePreviewDialogState();
}

class _GalleryImagePreviewDialogState extends State<_GalleryImagePreviewDialog> {
  late final PageController _pageController;
  late int index;

  @override
  void initState() {
    super.initState();
    index = widget.initialIndex;
    _pageController = PageController(initialPage: widget.initialIndex);
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.black,
      child: SafeArea(
        child: Stack(
          children: <Widget>[
            PageView.builder(
              controller: _pageController,
              itemCount: widget.paths.length,
              onPageChanged: (value) => setState(() => index = value),
              itemBuilder: (_, i) {
                final path = widget.paths[i];
                return InteractiveViewer(
                  minScale: 0.6,
                  maxScale: 5,
                  child: Center(
                    child: Image.file(
                      File(path),
                      fit: BoxFit.contain,
                      errorBuilder: (_, __, ___) => const Icon(Icons.broken_image, color: Colors.white, size: 64),
                    ),
                  ),
                );
              },
            ),
            Positioned(
              top: 8,
              right: 8,
              child: IconButton(
                onPressed: () => Navigator.pop(context),
                icon: const Icon(Icons.close, color: Colors.white, size: 32),
              ),
            ),
            Positioned(
              left: 0,
              right: 0,
              bottom: 18,
              child: Center(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                  decoration: BoxDecoration(color: Colors.black54, borderRadius: BorderRadius.circular(99)),
                  child: Text('${index + 1}/${widget.paths.length}', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900)),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
