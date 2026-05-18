# Modelesson Quest

A Flutter prototype for a soft dark/pixel todo app with gameplay progression.

## What is included

- Soft pixel dashboard UI based on the provided design
- Active quest list
- Quest creation form
- Priority system: low, normal, urgent
- EXP calculation
- Level and EXP progress
- Streak system
- Quest completion form with optional notes/photo
- Quest history page
- English / Indonesian language toggle
- Dark / light theme toggle
- LMS link button using `url_launcher`
- Local save using `shared_preferences`

## Folder structure

```text
lib/
  main.dart                    # app entry + shared imports/part files
  src/
    models.dart                # Quest, CompletedQuest, enums, EXP preview
    app_controller.dart        # save/load, quest logic, level/streak logic
    i18n.dart                  # English/Indonesian strings
    app_theme.dart             # dark/light theme and pixel text style
    app.dart                   # MaterialApp setup
    main_shell.dart            # bottom navigation + floating add button
    home_page.dart             # dashboard, stats, quest cards
    history_page.dart          # completed quest history
    settings_page.dart         # language/theme/reset settings
    create_quest_sheet.dart    # create quest bottom sheet
    complete_quest_sheet.dart  # complete quest bottom sheet
    pixel_widgets.dart         # reusable pixel panels/buttons/donut chart
    helpers.dart               # date helpers and LMS URL opener
```

This version uses Dart `part` files. That keeps the prototype easy to split and modify without needing many imports between files.

## Setup

Run these commands inside the project folder:

```bash
flutter clean
flutter pub get
flutter run
```

If you already opened the old version before, delete `pubspec.lock` first, then run `flutter pub get` again.

## Package compatibility note

The previous zip allowed `shared_preferences` to resolve to `2.5.4+`, which requires Dart SDK `>=3.9.0`. This version pins:

```yaml
shared_preferences: 2.5.3
image_picker: 1.1.2
url_launcher: 6.3.1
```

These are chosen to work with Dart SDK `3.8.1`.

## EXP rules currently implemented

```text
exp_needed = 100 + (44 * level)
```

Priority base EXP:

```text
low = 40
normal = 80
urgent = 120
```

Active quest EXP preview:

```text
progress_ratio = (duration_days - remaining_days) / duration_days
exp_gain = priority_base_exp * (1 + (progress_ratio * 3.0))
```

If the quest is overdue, completion gives:

```text
priority_base_exp * 0.5
```

The streak increases by 1 when a quest is completed before the deadline. If completed late, streak resets to 0.

## LMS upload limitation

The app can open the LMS link. It cannot reliably auto-fill a random external website image upload field, because websites handle upload fields differently and Flutter/browser security blocks automatic file injection in most cases.

Possible future solutions:

- manual upload after opening LMS
- LMS official API integration
- controlled WebView flow for a known LMS website
- share sheet export for photo/notes
