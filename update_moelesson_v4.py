from __future__ import annotations

import re
from pathlib import Path

ROOT = Path.cwd()
LIB = ROOT / "lib"
SRC = LIB / "src"

if not (ROOT / "pubspec.yaml").exists():
    raise SystemExit("Run this script from your Flutter project root, the folder that contains pubspec.yaml")
if not SRC.exists():
    raise SystemExit("Could not find lib/src. Run this inside the project that already has the v3 patch applied.")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    print("patched", path.relative_to(ROOT))


def backup(path: Path) -> None:
    if path.exists():
        bak = path.with_suffix(path.suffix + ".bak_v4")
        if not bak.exists():
            bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def ensure_import(text: str, import_line: str) -> str:
    if import_line in text:
        return text
    matches = list(re.finditer(r"^import .*?;\s*$", text, flags=re.M))
    if not matches:
        return import_line + "\n\n" + text
    pos = matches[-1].end()
    return text[:pos] + "\n" + import_line + text[pos:]


def replace_method(text: str, signature: str, new_method: str) -> str:
    start = text.find(signature)
    if start == -1:
        raise RuntimeError(f"Could not find method signature: {signature}")
    brace = text.find("{", start)
    if brace == -1:
        raise RuntimeError(f"Could not find opening brace for: {signature}")
    depth = 0
    i = brace
    in_string: str | None = None
    escape = False
    while i < len(text):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == in_string:
                in_string = None
        else:
            if ch in ("'", '"'):
                # Good enough for this generated Flutter code; avoids braces inside simple strings.
                in_string = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    return text[:start] + new_method.rstrip() + text[end:]
        i += 1
    raise RuntimeError(f"Could not find closing brace for: {signature}")


def patch_complete_quest_sheet() -> None:
    path = SRC / "complete_quest_sheet.dart"
    backup(path)
    text = read(path)
    text = ensure_import(text, "import 'package:flutter/services.dart';")

    guarded_show = r'''
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
'''.strip()

    text = re.sub(
        r"(?:bool _completeQuestSheetOpen = false;\s*)?(?:bool _globalImagePickerBusy = false;\s*)?Future<void> showCompleteQuestSheet\(BuildContext context, AppController controller, Quest quest\) async \{[\s\S]*?\n\}\n\nclass CompleteQuestSheet",
        guarded_show + "\n\nclass CompleteQuestSheet",
        text,
        count=1,
    )

    if "bool _isPickingImages = false;" not in text:
        text = text.replace(
            "  final photos = <String>[];",
            "  final photos = <String>[];\n  bool _isPickingImages = false;\n  bool _isFinishing = false;",
        )

    text = text.replace(
        "onTap: pickImages,",
        "onTap: (_isPickingImages || photos.length >= 10) ? null : pickImages,",
    )
    text = text.replace(
        "PixelButton(label: l.complete, filled: true, onPressed: finish),",
        "PixelButton(label: l.complete, filled: true, onPressed: _isFinishing ? null : finish),",
    )

    pick_images = r'''
  Future<void> pickImages() async {
    if (_isPickingImages || _globalImagePickerBusy || photos.length >= 10) return;
    setState(() => _isPickingImages = true);
    _globalImagePickerBusy = true;
    try {
      final picked = await picker.pickMultiImage(imageQuality: 82);
      if (!mounted || picked.isEmpty) return;
      final remainingSlots = 10 - photos.length;
      setState(() {
        for (final x in picked.take(remainingSlots)) {
          photos.add(x.path);
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
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Could not pick images: $e')));
    } finally {
      _globalImagePickerBusy = false;
      if (mounted) setState(() => _isPickingImages = false);
    }
  }
'''
    text = replace_method(text, "  Future<void> pickImages() async", pick_images)

    finish = r'''
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
'''
    text = replace_method(text, "  Future<void> finish() async", finish)
    write(path, text)


def patch_create_quest_sheet() -> None:
    path = SRC / "create_quest_sheet.dart"
    backup(path)
    text = read(path)

    guarded_show = r'''
bool _createQuestSheetOpen = false;

Future<void> showCreateQuestSheet(BuildContext context, AppController controller) async {
  if (_createQuestSheetOpen) return;
  _createQuestSheetOpen = true;
  try {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => CreateQuestSheet(controller: controller),
    );
  } finally {
    _createQuestSheetOpen = false;
  }
}
'''.strip()
    text = re.sub(
        r"(?:bool _createQuestSheetOpen = false;\s*)?Future<void> showCreateQuestSheet\(BuildContext context, AppController controller\) async \{[\s\S]*?\n\}\n\nclass CreateQuestSheet",
        guarded_show + "\n\nclass CreateQuestSheet",
        text,
        count=1,
    )

    if "bool _isSaving = false;" not in text:
        text = text.replace(
            "  DateTime deadline = DateTime.now().add(const Duration(days: 7));",
            "  DateTime deadline = DateTime.now().add(const Duration(days: 7));\n  bool _isSaving = false;",
        )

    text = text.replace(
        "PixelButton(label: l.save, filled: true, onPressed: saveQuest),",
        "PixelButton(label: l.save, filled: true, onPressed: _isSaving ? null : saveQuest),",
    )

    pick_deadline = r'''
  Future<void> pickDeadline() async {
    final now = DateTime.now();
    final firstDate = DateTime(now.year, now.month, now.day);
    final lastDate = firstDate.add(Duration(days: priority.maxDeadlineDays));
    var initialDate = DateTime(deadline.year, deadline.month, deadline.day);
    if (initialDate.isBefore(firstDate)) initialDate = firstDate;
    if (initialDate.isAfter(lastDate)) initialDate = lastDate;

    final date = await showDatePicker(
      context: context,
      initialDate: initialDate,
      firstDate: firstDate,
      lastDate: lastDate,
    );
    if (date == null || !mounted) return;
    final time = await showTimePicker(context: context, initialTime: TimeOfDay.fromDateTime(deadline));
    if (time == null || !mounted) return;
    setState(() => deadline = DateTime(date.year, date.month, date.day, time.hour, time.minute));
  }
'''
    text = replace_method(text, "  Future<void> pickDeadline() async", pick_deadline)

    save_quest = r'''
  Future<void> saveQuest() async {
    if (_isSaving) return;
    FocusScope.of(context).unfocus();

    final cleanedTitle = title.text.trim();
    final cleanedUrl = fullUrl.text.trim();
    final cleanedId = lmsId.text.trim();

    void showError(String message) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    }

    if (cleanedTitle.isEmpty) {
      showError('Please fill the quest name first.');
      return;
    }

    if (linkMode == LmsLinkMode.fullUrl && cleanedUrl.isNotEmpty) {
      final uri = Uri.tryParse(cleanedUrl);
      final valid = uri != null && (uri.isScheme('http') || uri.isScheme('https')) && uri.host.isNotEmpty;
      if (!valid) {
        showError('Invalid LMS link. Use a full URL like https://mylms.telkomschools.sch.id/...');
        return;
      }
    }

    if (linkMode == LmsLinkMode.moodleId && cleanedId.isNotEmpty && !RegExp(r'^\d+$').hasMatch(cleanedId)) {
      showError('LMS ID must contain numbers only. You can also leave it empty.');
      return;
    }

    if (deadline.isBefore(DateTime.now().subtract(const Duration(minutes: 1)))) {
      showError('Deadline cannot be in the past.');
      return;
    }

    setState(() => _isSaving = true);
    try {
      final quest = Quest(
        id: newId(),
        title: cleanedTitle,
        description: desc.text.trim(),
        priority: priority,
        workType: workType,
        createdAt: DateTime.now(),
        deadline: deadline,
        lmsLinkMode: linkMode,
        lmsFullUrl: cleanedUrl,
        lmsActivityType: activityType,
        lmsId: cleanedId,
      );
      final err = await widget.controller.addQuest(quest);
      if (!mounted) return;
      if (err != null) {
        showError(err);
        return;
      }
      Navigator.pop(context);
    } catch (e) {
      if (!mounted) return;
      showError('Could not create quest: $e');
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }
'''
    text = replace_method(text, "  Future<void> saveQuest() async", save_quest)
    write(path, text)


def patch_helpers() -> None:
    path = SRC / "helpers.dart"
    backup(path)
    text = read(path)
    text = ensure_import(text, "import 'package:url_launcher/url_launcher.dart';")
    if "Future<void> openExternalLink" not in text:
        text += r'''

Future<void> openExternalLink(BuildContext context, String rawUrl) async {
  final cleaned = rawUrl.trim();
  if (cleaned.isEmpty) {
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('No LMS link was added for this quest.')));
    return;
  }

  final uri = Uri.tryParse(cleaned);
  final valid = uri != null && (uri.isScheme('http') || uri.isScheme('https')) && uri.host.isNotEmpty;
  if (!valid) {
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Invalid LMS link.')));
    return;
  }

  try {
    final opened = await launchUrl(uri, mode: LaunchMode.externalApplication);
    if (!opened && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Could not open LMS link.')));
    }
  } catch (e) {
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Could not open LMS link: $e')));
  }
}
'''
    write(path, text)


def patch_quest_card() -> None:
    path = SRC / "quest_card.dart"
    backup(path)
    text = read(path)
    text = text.replace(
        "onPressed: () => launchUrl(Uri.parse(quest.lmsUrl), mode: LaunchMode.externalApplication)",
        "onPressed: () => openExternalLink(context, quest.lmsUrl)",
    )
    write(path, text)


def patch_gallery_page() -> None:
    path = SRC / "gallery_page.dart"
    if not path.exists():
        return
    backup(path)
    text = read(path)
    text = ensure_import(text, "import 'helpers.dart';")
    text = text.replace(
        "onPressed: () => launchUrl(Uri.parse(q.lmsUrl), mode: LaunchMode.externalApplication)",
        "onPressed: () => openExternalLink(context, q.lmsUrl)",
    )
    write(path, text)


def patch_models() -> None:
    path = SRC / "models.dart"
    backup(path)
    text = read(path)
    old = """    final cleanId = lmsId.trim();\n    if (cleanId.isEmpty) return '';\n    final type = lmsActivityType == LmsActivityType.assign ? 'assign' : 'quiz';"""
    new = r"""    final cleanId = lmsId.trim();
    if (cleanId.isEmpty || !RegExp(r'^\d+$').hasMatch(cleanId)) return '';
    final type = lmsActivityType == LmsActivityType.assign ? 'assign' : 'quiz';"""
    text = text.replace(r"RegExp(r'^\\d+\$').hasMatch(cleanId)", r"RegExp(r'^\\d+$').hasMatch(cleanId)")
    if old in text and "RegExp(r'^\\d+$').hasMatch(cleanId)" not in text:
        text = text.replace(old, new)
    write(path, text)


def patch_theme_and_fonts() -> None:
    path = SRC / "app_theme.dart"
    backup(path)
    text = read(path)
    # Improve Visitor TT2 baseline/line-height and clamp uneven text metrics without changing the font choice.
    if "final rawText = base.textTheme.apply" not in text:
        marker = "  return base.copyWith(\n"
        insert = r'''
  final rawText = base.textTheme.apply(fontFamily: family, bodyColor: colors.text, displayColor: colors.text);
  final fixedText = rawText.copyWith(
    displayLarge: rawText.displayLarge?.copyWith(height: 1.18),
    displayMedium: rawText.displayMedium?.copyWith(height: 1.18),
    displaySmall: rawText.displaySmall?.copyWith(height: 1.18),
    headlineLarge: rawText.headlineLarge?.copyWith(height: 1.16),
    headlineMedium: rawText.headlineMedium?.copyWith(height: 1.16),
    headlineSmall: rawText.headlineSmall?.copyWith(height: 1.16),
    titleLarge: rawText.titleLarge?.copyWith(height: 1.15),
    titleMedium: rawText.titleMedium?.copyWith(height: 1.15),
    titleSmall: rawText.titleSmall?.copyWith(height: 1.15),
    bodyLarge: rawText.bodyLarge?.copyWith(height: 1.18),
    bodyMedium: rawText.bodyMedium?.copyWith(height: 1.18),
    bodySmall: rawText.bodySmall?.copyWith(height: 1.18),
    labelLarge: rawText.labelLarge?.copyWith(height: 1.14),
    labelMedium: rawText.labelMedium?.copyWith(height: 1.14),
    labelSmall: rawText.labelSmall?.copyWith(height: 1.14),
  );
'''
        if marker in text:
            text = text.replace(marker, insert + marker, 1)
        text = text.replace(
            "textTheme: base.textTheme.apply(fontFamily: family, bodyColor: colors.text, displayColor: colors.text),",
            "textTheme: fixedText,",
        )
    write(path, text)


def patch_app_text_scaling() -> None:
    path = SRC / "app.dart"
    backup(path)
    text = read(path)
    if "TextScaler.linear(1.0)" not in text:
        text = text.replace(
            "      title: 'QuestClass',\n",
            "      title: 'QuestClass',\n      builder: (context, child) {\n        final media = MediaQuery.of(context);\n        return MediaQuery(\n          data: media.copyWith(textScaler: const TextScaler.linear(1.0)),\n          child: child ?? const SizedBox.shrink(),\n        );\n      },\n",
            1,
        )
    write(path, text)


def patch_sizes() -> None:
    replacements = [
        (SRC / "main_shell.dart", {
            "fontSize: 46": "fontSize: 40",
            "fontSize: 34": "fontSize: 32",
            "fontSize: 36": "fontSize: 34",
        }),
        (SRC / "stats_card.dart", {
            "fontSize: 48": "fontSize: 40",
            "fontSize: 24": "fontSize: 22",
            "fontSize: 20": "fontSize: 18",
        }),
        (SRC / "pixel_widgets.dart", {
            "fontSize: 26": "fontSize: 23",
            "fontSize: 24": "fontSize: 22",
        }),
        (SRC / "quest_card.dart", {
            "fontSize: compact ? 14 : 24": "fontSize: compact ? 13 : 21",
            "fontSize: 22": "fontSize: 20",
        }),
        (SRC / "home_page.dart", {
            "width: 70,\n        height: 70,": "width: 60,\n        height: 60,",
            "child: const Icon(Icons.add, size: 38)": "child: const Icon(Icons.add, size: 30)",
        }),
    ]
    for path, mapping in replacements:
        if not path.exists():
            continue
        backup(path)
        text = read(path)
        for old, new in mapping.items():
            text = text.replace(old, new)
        write(path, text)


patch_complete_quest_sheet()
patch_create_quest_sheet()
patch_helpers()
patch_quest_card()
patch_gallery_page()
patch_models()
patch_theme_and_fonts()
patch_app_text_scaling()
patch_sizes()

print("""
DONE v4.

Now run:
  flutter clean
  flutter pub get
  flutter run

What this fixes:
- Prevents double-tap / too-fast-click crashes for create sheet, complete sheet, image picker, save, and complete.
- Handles ImagePicker already_active with a friendly message instead of crashing.
- Allows empty LMS ID safely; invalid non-number IDs now show a friendly message.
- Validates full LMS URLs before saving/opening.
- Makes Visitor TT2 text sizing/baseline more stable and reduces the largest UI text a bit.
- Makes the plus button smaller again.

Backups were saved beside patched files as *.bak_v4 the first time this script touched them.
""")
