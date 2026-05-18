
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
                decoration: const BoxDecoration(color: Colors.black54, borderRadius: BorderRadius.only(bottomLeft: Radius.circular(10), topRight: Radius.circular(14))),
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
