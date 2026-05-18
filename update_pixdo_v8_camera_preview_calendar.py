from __future__ import annotations

import re
from pathlib import Path

ROOT = Path.cwd()
SRC = ROOT / "lib" / "src"

if not (ROOT / "pubspec.yaml").exists():
    raise SystemExit("Run this script from your Flutter project root, the folder that contains pubspec.yaml")
if not SRC.exists():
    raise SystemExit("Could not find lib/src. Run this inside your current PIXDO Flutter project.")


def backup(path: Path) -> None:
    if path.exists():
        bak = path.with_suffix(path.suffix + ".bak_v8")
        if not bak.exists():
            bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    backup(path)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    print("patched", path.relative_to(ROOT))


def replace_calendar_height() -> None:
    path = SRC / "home_page.dart"
    if not path.exists():
        print("warning: home_page.dart not found")
        return
    text = read(path)
    new = re.sub(
        r"SizedBox\(height:\s*compact\s*\?\s*\d+(?:\.0)?\s*:\s*\d+(?:\.0)?\s*,\s*child:\s*CalendarCard\(controller:\s*controller\)\)",
        "SizedBox(height: compact ? 430 : 500, child: CalendarCard(controller: controller))",
        text,
        count=1,
    )
    if new == text:
        print("warning: calendar height pattern not found in home_page.dart")
    else:
        write(path, new)


COMPLETE_QUEST_SHEET = r'''
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'i18n.dart';
import 'models.dart';
import 'pixel_widgets.dart';

bool _completeQuestSheetOpen = false;
bool _globalImagePickerBusy = false;

Future<void> showCompleteQuestSheet(BuildContext context, AppController controller, Quest quest) async {
  if (_completeQuestSheetOpen) return;
  _completeQuestSheetOpen = true;
  try {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => CompleteQuestSheet(controller: controller, quest: quest),
    );
  } finally {
    _completeQuestSheetOpen = false;
  }
}

class CompleteQuestSheet extends StatefulWidget {
  const CompleteQuestSheet({super.key, required this.controller, required this.quest});
  final AppController controller;
  final Quest quest;

  @override
  State<CompleteQuestSheet> createState() => _CompleteQuestSheetState();
}

class _CompleteQuestSheetState extends State<CompleteQuestSheet> {
  final notes = TextEditingController();
  final picker = ImagePicker();
  final photos = <String>[];
  bool _isPickingImages = false;
  bool _isFinishing = false;

  bool get _canAddMorePhotos => photos.length < 10 && !_isPickingImages && !_isFinishing;

  @override
  void dispose() {
    notes.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l = L10n(widget.controller.settings.language);
    final c = appColors(context);
    final isId = l.id;
    return Container(
      decoration: BoxDecoration(color: c.panel, borderRadius: const BorderRadius.vertical(top: Radius.circular(32))),
      padding: EdgeInsets.only(left: 20, right: 20, top: 20, bottom: MediaQuery.viewInsetsOf(context).bottom + 20),
      child: SafeArea(
        top: false,
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              Center(child: Container(width: 90, height: 5, decoration: BoxDecoration(color: c.line, borderRadius: BorderRadius.circular(99)))),
              const SizedBox(height: 18),
              Text(
                widget.quest.title.toUpperCase(),
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w900, letterSpacing: 2, height: 1.05),
              ),
              const SizedBox(height: 14),
              TextField(
                controller: notes,
                minLines: 3,
                maxLines: 6,
                decoration: InputDecoration(labelText: l.notesOptional, border: const OutlineInputBorder()),
              ),
              const SizedBox(height: 12),
              Row(
                children: <Widget>[
                  Expanded(child: Text(l.photosOptional, style: const TextStyle(fontWeight: FontWeight.w900))),
                  Text('${photos.length}/10', style: TextStyle(color: c.muted, fontWeight: FontWeight.w900)),
                ],
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: <Widget>[
                  for (int i = 0; i < photos.length; i++)
                    _PickedPhotoTile(
                      path: photos[i],
                      onPreview: () => showImagePreview(context, photos, i),
                      onRemove: _isFinishing ? null : () => setState(() => photos.removeAt(i)),
                    ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: <Widget>[
                  Expanded(
                    child: PixelButton(
                      label: _isPickingImages ? (isId ? 'TUNGGU...' : 'WAIT...') : (isId ? 'GALERI' : 'GALLERY'),
                      icon: Icons.photo_library_rounded,
                      onPressed: _canAddMorePhotos ? pickImagesFromGallery : null,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: PixelButton(
                      label: _isPickingImages ? (isId ? 'TUNGGU...' : 'WAIT...') : (isId ? 'KAMERA' : 'CAMERA'),
                      icon: Icons.photo_camera_rounded,
                      onPressed: _canAddMorePhotos ? takePhotoWithCamera : null,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 18),
              PixelButton(label: _isFinishing ? (isId ? 'MENYIMPAN...' : 'SAVING...') : l.complete, filled: true, onPressed: _isFinishing ? null : finish),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> pickImagesFromGallery() async {
    await _runImagePicker(() async {
      final picked = await picker.pickMultiImage(imageQuality: 82);
      return picked.map((x) => x.path).toList();
    });
  }

  Future<void> takePhotoWithCamera() async {
    await _runImagePicker(() async {
      final picked = await picker.pickImage(source: ImageSource.camera, imageQuality: 82);
      return picked == null ? <String>[] : <String>[picked.path];
    });
  }

  Future<void> _runImagePicker(Future<List<String>> Function() pickerAction) async {
    if (_isPickingImages || _globalImagePickerBusy || photos.length >= 10) return;
    setState(() => _isPickingImages = true);
    _globalImagePickerBusy = true;
    try {
      final pickedPaths = await pickerAction();
      if (!mounted || pickedPaths.isEmpty) return;
      final remainingSlots = 10 - photos.length;
      setState(() {
        for (final path in pickedPaths.take(remainingSlots)) {
          photos.add(path);
        }
      });
    } on PlatformException catch (e) {
      if (!mounted) return;
      final message = e.code == 'already_active'
          ? 'Image picker is already open. Please wait a second and try again.'
          : 'Could not open image picker: ${e.message ?? e.code}';
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Could not pick image: $e')));
    } finally {
      _globalImagePickerBusy = false;
      if (mounted) setState(() => _isPickingImages = false);
    }
  }

  Future<void> finish() async {
    if (_isFinishing) return;
    setState(() => _isFinishing = true);
    try {
      await widget.controller.completeQuest(widget.quest.id, notes: notes.text.trim(), photoPaths: photos);
      if (!mounted) return;
      Navigator.pop(context);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Could not complete quest: $e')));
    } finally {
      if (mounted) setState(() => _isFinishing = false);
    }
  }
}

class _PickedPhotoTile extends StatelessWidget {
  const _PickedPhotoTile({required this.path, required this.onPreview, required this.onRemove});
  final String path;
  final VoidCallback onPreview;
  final VoidCallback? onRemove;

  @override
  Widget build(BuildContext context) {
    final c = appColors(context);
    return Stack(
      children: <Widget>[
        InkWell(
          borderRadius: BorderRadius.circular(14),
          onTap: onPreview,
          child: ClipRRect(
            borderRadius: BorderRadius.circular(14),
            child: Image.file(
              File(path),
              width: 74,
              height: 74,
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => Container(
                width: 74,
                height: 74,
                alignment: Alignment.center,
                decoration: BoxDecoration(border: Border.all(color: c.line, width: 2), borderRadius: BorderRadius.circular(14)),
                child: const Icon(Icons.broken_image),
              ),
            ),
          ),
        ),
        if (onRemove != null)
          Positioned(
            right: 0,
            top: 0,
            child: InkWell(
              onTap: onRemove,
              child: Container(
                decoration: const BoxDecoration(color: Colors.black65, borderRadius: BorderRadius.only(bottomLeft: Radius.circular(10), topRight: Radius.circular(14))),
                padding: const EdgeInsets.all(3),
                child: const Icon(Icons.close, size: 18, color: Colors.white),
              ),
            ),
          ),
      ],
    );
  }
}

Future<void> showImagePreview(BuildContext context, List<String> paths, int initialIndex) async {
  if (paths.isEmpty) return;
  final safeInitial = initialIndex.clamp(0, paths.length - 1);
  await showDialog<void>(
    context: context,
    barrierColor: Colors.black87,
    builder: (_) => _ImagePreviewDialog(paths: List<String>.from(paths), initialIndex: safeInitial),
  );
}

class _ImagePreviewDialog extends StatefulWidget {
  const _ImagePreviewDialog({required this.paths, required this.initialIndex});
  final List<String> paths;
  final int initialIndex;

  @override
  State<_ImagePreviewDialog> createState() => _ImagePreviewDialogState();
}

class _ImagePreviewDialogState extends State<_ImagePreviewDialog> {
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
'''


HISTORY_PAGE = r'''
import 'dart:io';

import 'package:flutter/material.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'complete_quest_sheet.dart';
import 'helpers.dart';
import 'i18n.dart';
import 'pixel_widgets.dart';

class HistoryPage extends StatelessWidget {
  const HistoryPage({super.key, required this.controller});
  final AppController controller;

  @override
  Widget build(BuildContext context) {
    final l = L10n(controller.settings.language);
    final c = appColors(context);
    final items = controller.completedQuests();
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: ListView(
        padding: const EdgeInsets.fromLTRB(22, 18, 22, 120),
        children: <Widget>[
          SectionTitle(l.history),
          if (items.isEmpty)
            Center(child: Padding(padding: const EdgeInsets.all(40), child: Text(l.noQuest)))
          else
            for (final q in items)
              Container(
                margin: const EdgeInsets.only(bottom: 14),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: c.panel.withValues(alpha: 0.85),
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(color: c.line.withValues(alpha: 0.6), width: 2),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
                      children: <Widget>[
                        Expanded(
                          child: Text(
                            q.title.toUpperCase(),
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontSize: 22, height: 1.0, fontWeight: FontWeight.w900, letterSpacing: 2),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                          decoration: BoxDecoration(
                            color: q.wasLateCompleted()
                                ? const Color(0xFFFF4C67).withValues(alpha: 0.18)
                                : const Color(0xFF00FF39).withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(99),
                          ),
                          child: Text(
                            q.wasLateCompleted() ? l.completedLate : l.completedOnTime,
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w900,
                              color: q.wasLateCompleted() ? const Color(0xFFFF4C67) : const Color(0xFF00FF39),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text('${l.completed}: ${formatDateTime(q.completedAt ?? q.deadline)}'),
                    const SizedBox(height: 4),
                    Text('${l.expGained}: +${q.historyExp()} EXP', style: const TextStyle(fontWeight: FontWeight.w900)),
                    if (q.completionNotes.trim().isNotEmpty) ...<Widget>[
                      const SizedBox(height: 10),
                      Text(q.completionNotes),
                    ],
                    if (q.photoPaths.isNotEmpty) ...<Widget>[
                      const SizedBox(height: 12),
                      Text(
                        l.id ? 'Tap gambar untuk preview' : 'Tap image to preview',
                        style: TextStyle(color: c.muted, fontSize: 12, fontWeight: FontWeight.w900),
                      ),
                      const SizedBox(height: 8),
                      SizedBox(
                        height: 92,
                        child: ListView.separated(
                          scrollDirection: Axis.horizontal,
                          itemBuilder: (_, i) => InkWell(
                            borderRadius: BorderRadius.circular(12),
                            onTap: () => showImagePreview(context, q.photoPaths, i),
                            child: ClipRRect(
                              borderRadius: BorderRadius.circular(12),
                              child: Image.file(
                                File(q.photoPaths[i]),
                                width: 92,
                                height: 92,
                                fit: BoxFit.cover,
                                errorBuilder: (_, __, ___) => Container(
                                  width: 92,
                                  height: 92,
                                  alignment: Alignment.center,
                                  decoration: BoxDecoration(border: Border.all(color: c.line, width: 2), borderRadius: BorderRadius.circular(12)),
                                  child: const Icon(Icons.broken_image),
                                ),
                              ),
                            ),
                          ),
                          separatorBuilder: (_, __) => const SizedBox(width: 8),
                          itemCount: q.photoPaths.length,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
        ],
      ),
    );
  }
}
'''


CALENDAR_CARD = r'''
import 'package:flutter/material.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'i18n.dart';
import 'pixel_widgets.dart';

class CalendarCard extends StatefulWidget {
  const CalendarCard({super.key, required this.controller});
  final AppController controller;

  @override
  State<CalendarCard> createState() => _CalendarCardState();
}

class _CalendarCardState extends State<CalendarCard> {
  late DateTime month;
  DateTime? selected;

  @override
  void initState() {
    super.initState();
    month = DateTime(2026, 5);
  }

  @override
  Widget build(BuildContext context) {
    final l = L10n(widget.controller.settings.language);
    final c = appColors(context);
    final days = DateUtils.getDaysInMonth(month.year, month.month);
    final firstWeekday = DateTime(month.year, month.month, 1).weekday; // Monday = 1
    final active = widget.controller.activeQuests();
    final selectedTasks = selected == null
        ? <dynamic>[]
        : active.where((q) => DateUtils.isSameDay(q.deadline, selected)).toList();

    return PixelPanel(
      title: l.calendar,
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 16),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final compact = constraints.maxWidth < 380 || constraints.maxHeight < 420;
          final titleFont = compact ? 24.0 : 28.0;
          final weekFont = compact ? 13.0 : 15.0;
          final dayFont = compact ? 18.0 : 21.0;
          final navSize = compact ? 42.0 : 48.0;
          final dotSize = compact ? 7.0 : 8.0;

          Widget dayCell(int index) {
            final day = index - (firstWeekday - 1) + 1;
            if (day < 1 || day > days) {
              return const Expanded(child: SizedBox.shrink());
            }

            final date = DateTime(month.year, month.month, day);
            final count = active.where((q) => DateUtils.isSameDay(q.deadline, date)).length;
            final isToday = DateUtils.isSameDay(date, DateTime.now());
            final isSelected = selected != null && DateUtils.isSameDay(date, selected);

            return Expanded(
              child: Padding(
                padding: EdgeInsets.all(compact ? 2 : 3),
                child: Material(
                  color: isSelected ? c.line.withValues(alpha: 0.18) : Colors.transparent,
                  borderRadius: BorderRadius.circular(13),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(13),
                    onTap: () => setState(() => selected = date),
                    child: Container(
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(13),
                        border: isToday ? Border.all(color: c.accent, width: 2) : null,
                      ),
                      padding: const EdgeInsets.symmetric(vertical: 3, horizontal: 2),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: <Widget>[
                          SizedBox(
                            height: compact ? 22 : 26,
                            child: Center(
                              child: FittedBox(
                                fit: BoxFit.scaleDown,
                                child: Text(
                                  '$day',
                                  maxLines: 1,
                                  style: TextStyle(
                                    fontSize: dayFont,
                                    height: 1.0,
                                    fontWeight: FontWeight.w900,
                                    letterSpacing: 0.8,
                                    color: c.text,
                                  ),
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(height: 4),
                          SizedBox(
                            height: dotSize,
                            child: count > 0
                                ? Center(
                                    child: Container(
                                      width: dotSize,
                                      height: dotSize,
                                      decoration: const BoxDecoration(color: Color(0xFFFFC400), shape: BoxShape.circle),
                                    ),
                                  )
                                : const SizedBox.shrink(),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            );
          }

          return Column(
            children: <Widget>[
              SizedBox(
                height: compact ? 50 : 58,
                child: Row(
                  children: <Widget>[
                    _CalendarNavButton(
                      size: navSize,
                      icon: Icons.chevron_left,
                      onTap: () => setState(() => month = DateTime(month.year, month.month - 1)),
                    ),
                    Expanded(
                      child: Center(
                        child: FittedBox(
                          fit: BoxFit.scaleDown,
                          child: Text(
                            '${l.monthName(month.month)} ${month.year}',
                            maxLines: 1,
                            style: TextStyle(fontSize: titleFont, height: 1.0, fontWeight: FontWeight.w900, letterSpacing: 2.0, color: c.text),
                          ),
                        ),
                      ),
                    ),
                    _CalendarNavButton(
                      size: navSize,
                      icon: Icons.chevron_right,
                      onTap: () => setState(() => month = DateTime(month.year, month.month + 1)),
                    ),
                  ],
                ),
              ),
              SizedBox(
                height: compact ? 28 : 32,
                child: Row(
                  children: <Widget>[
                    _Week('M', fontSize: weekFont),
                    _Week('T', fontSize: weekFont),
                    _Week('W', fontSize: weekFont),
                    _Week('T', fontSize: weekFont),
                    _Week('F', fontSize: weekFont),
                    _Week('S', fontSize: weekFont),
                    _Week('S', fontSize: weekFont),
                  ],
                ),
              ),
              const SizedBox(height: 6),
              Expanded(
                child: Column(
                  children: List<Widget>.generate(6, (row) {
                    return Expanded(
                      child: Row(
                        children: List<Widget>.generate(7, (col) => dayCell(row * 7 + col)),
                      ),
                    );
                  }),
                ),
              ),
              if (selectedTasks.isNotEmpty) ...<Widget>[
                const SizedBox(height: 8),
                SizedBox(
                  height: 38,
                  child: ListView(
                    scrollDirection: Axis.horizontal,
                    children: selectedTasks
                        .map<Widget>((q) => Padding(
                              padding: const EdgeInsets.only(right: 8),
                              child: Chip(label: Text(q.title, overflow: TextOverflow.ellipsis)),
                            ))
                        .toList(),
                  ),
                ),
              ],
            ],
          );
        },
      ),
    );
  }
}

class _CalendarNavButton extends StatelessWidget {
  const _CalendarNavButton({required this.size, required this.icon, required this.onTap});
  final double size;
  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final c = appColors(context);
    return SizedBox(
      width: size,
      height: size,
      child: OutlinedButton(
        onPressed: onTap,
        style: OutlinedButton.styleFrom(
          padding: EdgeInsets.zero,
          side: BorderSide(color: c.line.withValues(alpha: 0.7), width: 2),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          foregroundColor: c.text,
        ),
        child: Icon(icon, size: size * 0.62),
      ),
    );
  }
}

class _Week extends StatelessWidget {
  const _Week(this.text, {required this.fontSize});
  final String text;
  final double fontSize;

  @override
  Widget build(BuildContext context) {
    final c = appColors(context);
    return Expanded(
      child: Center(
        child: Text(
          text,
          style: TextStyle(fontWeight: FontWeight.w900, fontSize: fontSize, height: 1.0, color: c.muted),
        ),
      ),
    );
  }
}
'''


def patch_ios_permissions() -> None:
    plist = ROOT / "ios" / "Runner" / "Info.plist"
    if not plist.exists():
        return
    text = read(plist)
    insert = ""
    if "NSCameraUsageDescription" not in text:
        insert += "\n\t<key>NSCameraUsageDescription</key>\n\t<string>PIXDO needs camera access so you can take quest completion photos.</string>"
    if "NSPhotoLibraryUsageDescription" not in text:
        insert += "\n\t<key>NSPhotoLibraryUsageDescription</key>\n\t<string>PIXDO needs photo access so you can attach quest completion images.</string>"
    if insert:
        text = text.replace("</dict>", insert + "\n</dict>", 1)
        write(plist, text)


def patch_android_permissions() -> None:
    manifest = ROOT / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
    if not manifest.exists():
        return
    text = read(manifest)
    changed = False
    if "android.permission.CAMERA" not in text:
        text = text.replace("<application", "    <uses-permission android:name=\"android.permission.CAMERA\" />\n\n    <application", 1)
        changed = True
    if changed:
        write(manifest, text)


def main() -> None:
    write(SRC / "complete_quest_sheet.dart", COMPLETE_QUEST_SHEET)
    write(SRC / "history_page.dart", HISTORY_PAGE)
    write(SRC / "calendar_card.dart", CALENDAR_CARD)
    replace_calendar_height()
    patch_android_permissions()
    patch_ios_permissions()
    print("""
DONE v8.

Now run:
  flutter clean
  flutter pub get
  flutter run

Changes:
- Complete quest now supports both GALLERY and CAMERA.
- Image picker is still protected from fast double-click / already_active crashes.
- History images can be tapped for fullscreen preview with zoom and swipe.
- Calendar navigation buttons are bigger and no longer shrink with the month text.
- Calendar orange dots now have their own reserved space under the day number.
- Calendar panel was made slightly taller to give the bigger text enough room.
""")


if __name__ == "__main__":
    main()
