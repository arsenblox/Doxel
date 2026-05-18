from __future__ import annotations

import re
from pathlib import Path

ROOT = Path.cwd()
SRC = ROOT / "lib" / "src"
PUBSPEC = ROOT / "pubspec.yaml"

if not PUBSPEC.exists():
    raise SystemExit("Run this script from your Flutter project root, the folder that contains pubspec.yaml")
if not SRC.exists():
    raise SystemExit("Could not find lib/src. Run this inside your current Flutter project.")


def backup(path: Path) -> None:
    if path.exists():
        bak = path.with_suffix(path.suffix + ".bak_v10")
        if not bak.exists():
            bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    backup(path)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    print("patched", path.relative_to(ROOT))


# Keep the app name as Doxel instead of forced all-caps where the display constant exists.
models_path = SRC / "models.dart"
if models_path.exists():
    text = read(models_path)
    text = re.sub(r"const\s+String\s+appDisplayName\s*=\s*['\"][^'\"]+['\"];", "const String appDisplayName = 'Doxel';", text)
    write(models_path, text)


controller_path = SRC / "app_controller.dart"
if not controller_path.exists():
    raise SystemExit("Could not find lib/src/app_controller.dart")

text = read(controller_path)

old_entries_pattern = re.compile(
    r"\s*a\('quest_1'.*?\n\s*a\('panic_solver'.*?\),",
    re.DOTALL,
)

new_entries = """
      a('quest_1', 'Quest Beginner', 'You completed your first quest.', completed, 1),
      a('quest_5', 'Quest Regular', 'You completed 5 quests.', completed, 5),
      a('quest_10', 'Quest Tracker', 'You completed 10 quests.', completed, 10),
      a('quest_25', 'Quest Finisher', 'You completed 25 quests.', completed, 25),
      a('quest_50', 'Quest Veteran', 'You completed 50 quests.', completed, 50),
      a('quest_100', 'Quest Master', 'You completed 100 quests.', completed, 100),
      a('level_2', 'Level 2 Reached', 'You reached level 2.', level, 2),
      a('level_5', 'Level 5 Reached', 'You reached level 5.', level, 5),
      a('level_10', 'Level 10 Reached', 'You reached level 10.', level, 10),
      a('level_25', 'Level 25 Reached', 'You reached level 25.', level, 25),
      a('level_50', 'Level 50 Reached', 'You reached level 50.', level, 50),
      a('level_100', 'Level 100 Reached', 'You reached level 100.', level, 100),
      a('streak_1', 'First Streak', 'You kept a 1-quest streak.', streak, 1),
      a('streak_5', '5 Streak', 'You kept a 5-quest streak.', streak, 5),
      a('streak_10', '10 Streak', 'You kept a 10-quest streak.', streak, 10),
      a('streak_15', '15 Streak', 'You kept a 15-quest streak.', streak, 15),
      a('streak_30', '30 Streak', 'You kept a 30-quest streak.', streak, 30),
      a('streak_60', '60 Streak', 'You kept a 60-quest streak.', streak, 60),
      a('streak_100', '100 Streak', 'You kept a 100-quest streak.', streak, 100),
      a('early_24h', 'Early Completion', 'Complete a quest at least 24 hours before the deadline.', early24, 1),
      a('miss_streak_1', 'Streak Lost', 'Lose your streak for the first time.', missed, 1),
      a('miss_deadline_1', 'Deadline Missed', 'Miss a quest deadline for the first time.', missed, 1),
      a('proof_sender', 'Image Attached', 'Complete a quest with at least one image attached.', withImages, 1),
      a('lore_writer', 'Notes Added', 'Complete a quest with notes attached.', withNotes, 1),
      a('panic_solver', 'Urgent Quest Completed', 'Complete an urgent quest on time.', urgentOnTime, 1),"""

if old_entries_pattern.search(text):
    text = old_entries_pattern.sub("\n" + new_entries, text)
else:
    # Fallback exact replacements, useful if the file was manually edited.
    replacements = {
        "'Quest Collector'": "'Quest Regular'",
        "'Five quests down. Your todo list is scared.'": "'You completed 5 quests.'",
        "'Quest Hunter'": "'Quest Tracker'",
        "'You completed 10 quests. Not bad, main character.'": "'You completed 10 quests.'",
        "'Homework Slayer'": "'Quest Finisher'",
        "'25 quests completed. You are actually grinding.'": "'You completed 25 quests.'",
        "'No-Life? Respect.'": "'Quest Veteran'",
        "'50 quests completed. That is kind of insane.'": "'You completed 50 quests.'",
        "'Quest Final Boss'": "'Quest Master'",
        "'100 quests completed. The checklist fears you.'": "'You completed 100 quests.'",
        "'GETTING STARTED | LEVEL 2'": "'Level 2 Reached'",
        "'You reached level 2. The tutorial is over.'": "'You reached level 2.'",
        "\"Oh wow, you're intermediate now | LEVEL 5\"": "'Level 5 Reached'",
        "'Level 5 reached. Your EXP bar is cooking.'": "'You reached level 5.'",
        "\"Damn, you're a Pro now | LEVEL 10\"": "'Level 10 Reached'",
        "'Level 10 reached. Certified quest enjoyer.'": "'You reached level 10.'",
        "'Homework Slayer | LEVEL 25'": "'Level 25 Reached'",
        "'Level 25 reached. The grind is getting serious.'": "'You reached level 25.'",
        "'Pixel Academic Weapon | LEVEL 50'": "'Level 50 Reached'",
        "'Level 50 reached. Your calendar needs backup.'": "'You reached level 50.'",
        "'DOXEL FINAL BOSS | LEVEL 100'": "'Level 100 Reached'",
        "'Level 100 reached. You beat the todo game.'": "'You reached level 100.'",
        "'Streak Spark'": "'First Streak'",
        "'One clean quest. Keep the flame alive.'": "'You kept a 1-quest streak.'",
        "'Streak Keeper'": "'5 Streak'",
        "'Five streak. Now it is becoming a habit.'": "'You kept a 5-quest streak.'",
        "'Streak Warrior'": "'10 Streak'",
        "'Ten streak. Deadlines are sweating.'": "'You kept a 10-quest streak.'",
        "'Calendar Bully'": "'15 Streak'",
        "'Fifteen streak. You bully your own schedule.'": "'You kept a 15-quest streak.'",
        "'Streak Demon'": "'30 Streak'",
        "'Thirty streak. You are locked in.'": "'You kept a 30-quest streak.'",
        "'Streak Monster'": "'60 Streak'",
        "'Sixty streak. That is discipline.'": "'You kept a 60-quest streak.'",
        "'STREAK GOD!'": "'100 Streak'",
        "'One hundred streak. Absolutely illegal behavior.'": "'You kept a 100-quest streak.'",
        "'Oops, Streak Gone'": "'Streak Lost'",
        "'Huh Loser..'": "'Deadline Missed'",
        "'Proof Sender'": "'Image Attached'",
        "'Lore Writer'": "'Notes Added'",
        "'Panic Solver'": "'Urgent Quest Completed'",
    }
    for a, b in replacements.items():
        text = text.replace(a, b)

write(controller_path, text)

print("\nDone. Achievement names are now more normal/clean.")
print("Run:")
print("flutter clean")
print("flutter pub get")
print("flutter run")
