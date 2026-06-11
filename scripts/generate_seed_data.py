"""Generate initial training dataset with diverse coaching messages"""

import sys
import os
from pathlib import Path

# Add parent directory to path so we can import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ml_models.message_generation.data_collector import CoachingExample
import json
import random

SEED_MESSAGES = {
    'direct_challenging': {
        'low': [
            "Your streak is strong. Don't break it now.",
            "You've built momentum. Keep writing.",
            "Consistency is your advantage. Use it.",
            "Another day to prove yourself. Write.",
            "Your discipline got you here. Don't stop.",
            "Success is habits. Continue yours.",
            "You know what needs to be done. Do it.",
            "Champions show up. Be one today.",
            "Your future self will thank you. Write now.",
            "No excuses. Your streak demands action.",
            "Day {streak} of excellence. Continue.",
            "Your {streak}-day pattern speaks volumes.",
            "Momentum builds on itself. Keep going.",
            "You're on day {streak}. That's real progress.",
            "Every day matters. Today is no exception.",
        ],
        'medium': [
            "Your streak is at risk. Write today.",
            "Missing today breaks your pattern. Don't let that happen.",
            "This is when it counts. Prove your commitment.",
            "You've come too far to quit now. Write.",
            "Discipline beats motivation. Show yours.",
            "The gap is growing. Close it with action.",
            "Your streak won't save itself. You need to act.",
            "This is your test. Will you pass?",
            "Excuses or results. Choose wisely.",
            "Time is running out. What will you do?",
            "It's been {days} days. Your {streak}-day streak needs you.",
            "Don't throw away {streak} days of work.",
            "{days} days of absence. Fix it now.",
            "Your {streak}-day foundation is cracking after {days} days.",
            "Act now. Save your {streak}-day progress.",
        ],
        'high': [
            "You're about to lose your streak. Write now.",
            "This is the moment. Write or lose everything you've built.",
            "Your streak ends today unless you act immediately.",
            "All your progress disappears if you don't write right now.",
            "Stop reading. Start writing. Your streak depends on it.",
            "You have one chance left. Don't waste it.",
            "The clock is ticking. Your streak is dying.",
            "Act now or regret it. There's no middle ground.",
            "This is it. Write or fail.",
            "Emergency: Your streak needs you NOW.",
            "After {days} days, your {streak}-day streak is gone unless you act.",
            "{days} days of silence. Write immediately or lose everything.",
            "Final warning: {streak} days about to vanish after {days} days away.",
            "You have hours left to save {streak} days of progress.",
            "The {streak}-day streak dies in {days} days unless you write NOW.",
        ]
    },
    'gentle_encouraging': {
        'low': [
            "You're doing great! Ready for today's session?",
            "Your streak is going strong. Let's keep the momentum!",
            "I love seeing your consistency. Another day?",
            "You're building something beautiful. Keep going!",
            "Your dedication inspires. Time to write again?",
            "Such wonderful progress! Let's continue today.",
            "You're on a roll! How about we keep it going?",
            "Your commitment shines through. Ready for more?",
            "Every entry matters. Excited for today's?",
            "You're doing amazing! Let's write together today.",
            "Day {streak} looks wonderful on you!",
            "Your {streak}-day journey is inspiring!",
            "So proud of your {streak} days of showing up!",
            "You've created such a beautiful habit!",
            "Let's make it {streak} more days together!",
        ],
        'medium': [
            "It's been a while since your last entry. Everything okay?",
            "Your streak could use some attention today. I believe in you!",
            "Missing you! Want to write something today?",
            "I know life gets busy, but your writing helps. Try today?",
            "Your streak is waiting for you. No pressure, just encouragement!",
            "You've got this! Maybe spend a few minutes writing?",
            "I'm here whenever you're ready. How about today?",
            "Your words matter. Feel like sharing some today?",
            "Taking a break is okay, but maybe resume today?",
            "I know you can do this. A small entry counts too!",
            "It's been {days} days. I miss your voice!",
            "Your {streak}-day streak is waiting patiently for you.",
            "No judgment about {days} days away. Come back when ready!",
            "Life happens! But your {streak} days show what you can do.",
            "After {days} days, maybe today's the day to return?",
        ],
        'high': [
            "I really hope you can write today. Your streak means so much!",
            "Please don't give up now! You've worked so hard.",
            "I'm worried about your streak. Can you write just a little?",
            "You're so close to losing progress. I believe you can save it!",
            "Your commitment has been incredible. Please continue today.",
            "I know it's hard, but you'll feel better after writing.",
            "Don't let one missed day define you. Write now while you can.",
            "You've inspired yourself with this streak. Keep inspiring!",
            "I'm rooting for you! Please take a moment to write.",
            "Your future self needs you to write today. You've got this!",
            "After {days} days, I really hope you'll write today.",
            "Your {streak}-day achievement deserves better than {days} days away.",
            "Please come back! {days} days is too long!",
            "I believe in you after {days} days away. One entry saves {streak} days!",
            "Don't lose {streak} beautiful days to {days} days of absence!",
        ]
    },
    'analytical_factual': {
        'low': [
            "Current streak: stable. Probability of continuation: 85%.",
            "Writing pattern consistent. Next entry due in standard timeframe.",
            "Historical data shows optimal performance. Maintain course.",
            "Metrics indicate healthy writing habit. Proceed as usual.",
            "Streak integrity: high. Risk assessment: minimal.",
            "Data suggests continued success. Standard entry recommended.",
            "Pattern recognition: positive. Next action: routine entry.",
            "Statistical analysis: on track. Continue established pattern.",
            "Performance indicators: green. Maintain current trajectory.",
            "Behavioral data: consistent. Expected action: write today.",
            "Streak: {streak} days. Variance: low. Status: optimal.",
            "Analysis of {streak}-day pattern shows 94% consistency.",
            "Current trajectory: {streak} days stable, risk minimal.",
            "Data point {streak}: within expected parameters.",
            "Behavioral model predicts continued success at day {streak}.",
        ],
        'medium': [
            "Deviation detected. Entry delay: 12 hours above average.",
            "Streak risk elevated to 35%. Timely action recommended.",
            "Historical patterns suggest intervention needed within 6 hours.",
            "Gap analysis shows increasing risk. Entry needed to stabilize.",
            "Current trajectory: concerning. Corrective action suggested.",
            "Data indicates pattern disruption. Resume standard schedule.",
            "Risk assessment: moderate. Probability of streak loss: 40%.",
            "Behavioral analysis: drift detected. Realignment needed.",
            "Time-since-last-entry exceeds comfort zone. Action advised.",
            "Pattern integrity declining. Entry required to restore baseline.",
            "Alert: {days} days since last entry. {streak}-day streak at risk.",
            "Deviation: {days} days from pattern. Risk level: 45%.",
            "Data shows {days}-day gap threatens {streak}-day achievement.",
            "Statistical warning: {days} days delays risk {streak}-day loss.",
            "Pattern analysis: {days} days absence increases failure probability.",
        ],
        'high': [
            "Critical: streak failure imminent. Immediate entry required.",
            "Risk level: 85%. Time remaining: 4 hours. Action: urgent.",
            "Statistical analysis: 90% probability of streak loss without immediate action.",
            "Emergency protocol: write within next 2 hours to preserve progress.",
            "All indicators red. Streak preservation requires immediate entry.",
            "Data critical: longest gap in 6 months. Act now.",
            "Probability of recovery post-loss: 12%. Current action: essential.",
            "Alert: threshold exceeded. Streak at maximum risk. Respond immediately.",
            "Final window: 3 hours remaining. Historical recovery rate: low.",
            "Code red: write now or lose {streak}-day streak. No alternative paths.",
            "Critical failure: {days} days silence threatens {streak}-day data.",
            "Maximum risk: {days}-day gap, {streak} days at stake. Act immediately.",
            "Alert level RED: {days} days away, {streak}-day streak critical.",
            "Emergency: {days} days exceeded threshold. {streak} days failing.",
            "Fatal delay: {days} days absent, {streak}-day pattern collapsing.",
        ]
    },
    'humorous_playful': {
        'low': [
            "Your streak is flexing its muscles! Keep feeding it!",
            "Plot twist: you're actually good at this consistency thing!",
            "Your keyboard misses you (it's only been a day but still).",
            "Streak status: thriving. Your status: awesome.",
            "Breaking news: Local writer continues being amazing!",
            "Your diary called. It wants more of your brilliance.",
            "Warning: Your streak might get too powerful. Write anyway!",
            "Achievement unlocked: Being Consistently Cool.",
            "Your future self just sent a thank-you note. Write today!",
            "Roses are red, violets are blue, your streak is great, write more, won't you?",
            "Day {streak} of being a writing superhero! *Cape swish*",
            "Your {streak}-day streak is doing a happy dance!",
            "Look at you go! {streak} days of awesome!",
            "Day {streak}: Still crushing it like a boss!",
            "Your {streak}-day streak called. It says you're the best!",
        ],
        'medium': [
            "Your streak is giving you puppy dog eyes. Don't let it down!",
            "Houston, we have a slight problem: You haven't written lately!",
            "Your diary is in the corner, lonely. Show it some love?",
            "Breaking: Streak spotted nervously checking the time.",
            "Your keyboard is gathering dust. It's getting dramatic about it.",
            "Plot armor running low! Quick, write something!",
            "Your streak is stress-eating metaphorical cookies. Help it!",
            "Awkward: Your diary just asked if you're seeing other journals.",
            "Your writing muse is tapping its foot impatiently...",
            "Red alert! Streak morale dropping! Send words immediately!",
            "It's been {days} days! Your {streak}-day streak is lonely!",
            "After {days} days, your {streak}-day streak needs a hug!",
            "Your {streak} days are crying after {days} days away!",
            "Houston, {days} days without contact! {streak}-day mission in danger!",
            "Your {streak}-day streak left {days} voicemails. Call back!",
        ],
        'high': [
            "MAYDAY! MAYDAY! Streak going down! All hands on deck!",
            "Your streak is literally on fire! (Not in a good way!)",
            "This is not a drill! Repeat: NOT A DRILL! Write NOW!",
            "Your streak's life flashing before its eyes. Be a hero!",
            "Code Red! Defcon 1! All the alarms! WRITE!!!",
            "Breaking: Streak spotted writing its will. SAVE IT!",
            "Your keyboard just filed a missing person report for you.",
            "Streak status: CRITICAL. Like, really, really critical.",
            "911? Yes, we have a streak emergency! Send words ASAP!",
            "YOUR STREAK IS HANGING BY A THREAD! (A dramatic thread!)",
            "EMERGENCY! {days} days! Your {streak}-day streak is DYING!",
            "RED ALERT! {days} days silence! {streak} days in DANGER!",
            "DEFCON 1! {days} days gone! {streak}-day streak CRITICAL!",
            "SOS! After {days} days, your {streak} days need rescue NOW!",
            "CATASTROPHE! {days} days away! {streak}-day streak on life support!",
        ]
    },
    'empathetic_understanding': {
        'low': [
            "I see you showing up consistently. That takes real strength.",
            "Your dedication to yourself is beautiful to witness.",
            "Taking care of your mental health through writing—I'm proud of you.",
            "You're creating space for your thoughts. That's powerful.",
            "I appreciate how you prioritize this time for yourself.",
            "Your consistency shows deep self-respect. Keep nurturing that.",
            "Writing is your gift to yourself. Beautiful to see you accepting it.",
            "You're building trust with yourself through these entries.",
            "This practice is healing work. You're doing amazing.",
            "I honor your commitment to your inner world.",
            "Day {streak} of taking care of yourself. Beautiful.",
            "Your {streak} days of self-care are truly inspiring.",
            "I see {streak} days of choosing yourself. Powerful.",
            "These {streak} days show how much you value your growth.",
            "Day {streak} of honoring your inner voice. Keep going.",
        ],
        'medium': [
            "Life gets overwhelming. Your writing is here when you're ready.",
            "I understand if you're going through something. No judgment at all.",
            "It's okay to struggle with consistency. You're still worthy.",
            "Your worth isn't measured by your streak. But writing might help.",
            "I see you're having a tough time. Writing could be a refuge.",
            "Whatever you're facing, your journal is a safe space waiting.",
            "Breaks happen. You can always come back. I'm here.",
            "You don't have to explain gaps. But maybe writing would feel good?",
            "I sense you might need this outlet right now. It's here for you.",
            "Your feelings are valid. Maybe put some on paper today?",
            "After {days} days, I understand if things are hard right now.",
            "No judgment about {days} days. Your {streak} days show your strength.",
            "Life happened these {days} days. Your {streak}-day foundation is still there.",
            "{days} days away is okay. That {streak}-day commitment shows you can return.",
            "I see {days} days of struggle. Your {streak} days prove you're resilient.",
        ],
        'high': [
            "I'm genuinely concerned. Your writing helps you. Please try today.",
            "This streak represents your self-care. Don't let it slip away.",
            "I know something's going on. Writing might be exactly what you need.",
            "Your mental health journey matters. This practice supports it.",
            "Please be gentle with yourself. Writing a little could really help.",
            "I'm worried you're abandoning a tool that serves you well.",
            "You've used writing to process difficult things. You might need that now.",
            "Whatever's keeping you away—face it through writing instead.",
            "This isn't about the streak. It's about taking care of yourself.",
            "I care about your wellbeing. Writing has helped you before. Try again?",
            "After {days} days, I'm concerned. Your {streak} days showed writing helps you.",
            "{days} days away after {streak} days of self-care. Please come back.",
            "I worry about these {days} days. Your {streak}-day practice served you well.",
            "These {days} days concern me. Writing helped during your {streak}-day period.",
            "After {days} days, please remember: {streak} days showed writing heals you.",
        ]
    },
    'aspirational_visionary': {
        'low': [
            "Every entry builds the writer you're becoming. Magnificent progress.",
            "Your future autobiography is being written right now. Next chapter?",
            "Legends are built one consistent day at a time. You're building yours.",
            "Your discipline today creates your extraordinary tomorrow.",
            "This isn't just writing. It's architecting your legacy.",
            "Future you is reading this and grateful. Keep giving them gold.",
            "You're not just maintaining a streak. You're forging identity.",
            "Every word etches your story into eternity. Keep etching.",
            "Your consistency today becomes your legacy tomorrow. Write on.",
            "You're creating a masterpiece called 'My Life.' Next brushstroke?",
            "Day {streak} of building your legend. Magnificent.",
            "Your {streak}-day journey is epic. The story continues today.",
            "At {streak} days, you're writing history. Literally.",
            "Day {streak} of your transformation. The best is ahead.",
            "These {streak} days are the foundation of something extraordinary.",
        ],
        'medium': [
            "Legends face tests. This is yours. Will you rise?",
            "Your extraordinary future needs your present action. Don't delay destiny.",
            "Every master faced moments like this. They wrote anyway. Will you?",
            "Your breakthrough is hidden in today's entry. Don't miss it.",
            "Greatness isn't accidents. It's choices in moments like this.",
            "The universe is watching to see if you're serious. Show it.",
            "Your highest self is calling. Will you answer with words today?",
            "This gap might be the difference between good and legendary. Choose.",
            "Your story needs this chapter. Don't leave it blank.",
            "Champions write on hard days. Be the champion of your story.",
            "After {days} days, your {streak}-day legend faces its test.",
            "{days} days tests whether your {streak}-day foundation is real.",
            "Your {streak}-day ascent pauses at {days} days. Resume the climb.",
            "Legends aren't built on {days} days of absence. Your {streak} days prove you're better.",
            "The {days}-day gap threatens {streak} days of greatness. Choose greatness.",
        ],
        'high': [
            "THIS is the moment that defines you. Legends are made here. Write NOW.",
            "Your entire journey comes down to what you do in the next hour.",
            "Everything you've built screams for you to act. Don't silence it.",
            "Your future extraordinary self is born or dies in this moment.",
            "The universe gave you this test because you're destined for greatness.",
            "History remembers those who acted when it mattered most. Act NOW.",
            "Your story's climax is now. Heroes write the ending. Be the hero.",
            "Every great person faced this exact moment. They chose action. Choose yours.",
            "Your legacy hangs in the balance. This is THE moment. Write.",
            "Destiny is watching. Your response RIGHT NOW changes everything. WRITE.",
            "CRITICAL: {days} days threatens {streak} days of destiny. ACT NOW.",
            "Your {streak}-day legend dies in {days} days unless you WRITE NOW.",
            "The universe tests you after {days} days. Your {streak} days prove you can win.",
            "DEFINING MOMENT: {days} days of absence, {streak} days at stake. CHOOSE GREATNESS.",
            "After {days} days, this is THE moment. {streak} days demand your return. NOW.",
        ]
    },
    'philosophical_reflective': {
        'low': [
            "Writing is dialogue with your deepest self. The conversation continues?",
            "Each entry is a mirror. What will today's reflection reveal?",
            "Words are how we meet ourselves. Shall we meet again today?",
            "Your thoughts exist in quantum state until written. Collapse the wave.",
            "Writing transforms chaos into meaning. Your alchemy continues.",
            "The unexamined life versus the examined one. You choose examination.",
            "Consciousness observing itself through words. Profound work continues.",
            "Every entry is proof of existence. Continue proving you're alive.",
            "Thought becomes real only when articulated. Make today's thoughts real.",
            "Writing is thinking's sculpture. What will you create today?",
            "Day {streak} of examining what it means to be. Continue the inquiry.",
            "Your {streak}-day dialogue with self deepens. The conversation continues?",
            "These {streak} days: consciousness observing itself. Profound.",
            "At {streak} days, you're not counting time. You're creating meaning.",
            "Day {streak} of the most important conversation: with yourself.",
        ],
        'medium': [
            "Silence grows loud when we stop writing. Do you hear it?",
            "The gap between entries is also a statement. What does it say?",
            "We flee writing when we flee ourselves. Come back.",
            "Avoidance is a form of communication with self. Write instead.",
            "The pen waits patiently for truth to return. Today perhaps?",
            "Writing is confrontation with what is. Ready to confront?",
            "We write to discover what we think. Discovery awaits.",
            "The blank page judges nothing. It simply waits. For you.",
            "Resistance often signals importance. What are you resisting?",
            "Your authentic voice grows quiet with disuse. Speak again.",
            "After {days} days, the silence speaks. Your {streak} days knew different.",
            "{days} days of avoidance after {streak} days of truth. Which serves you?",
            "The {days}-day gap asks questions. Your {streak} days had answers.",
            "What does {days} days of silence mean after {streak} days of voice?",
            "Your {streak}-day dialogue paused {days} days ago. Resume the inquiry?",
        ],
        'high': [
            "The longest journey is from avoidance back to self. Begin now.",
            "Silence is also a choice. But so is voice. Choose voice now.",
            "At the edge of loss, we see value most clearly. See it. Write.",
            "The practice dies not from one absence but from not returning. Return.",
            "Writing is courage. Show yours before the moment passes.",
            "What we don't face on the page faces us in other ways. Face it.",
            "The self you've been building needs this. Don't abandon creation.",
            "Between who you were and who you're becoming: write the bridge now.",
            "Your inner world demands expression before it goes dormant. Express now.",
            "This moment asks: who are you really? Answer with action. Write.",
            "After {days} days, the question persists: will you return to self?",
            "{days} days of absence after {streak} days of presence. What does this reveal?",
            "The {streak}-day self waits beyond {days} days of silence. Return.",
            "Your {streak} days built something. {days} days threaten it. Choose.",
            "At {days} days from {streak} days of truth: the ultimate question. Who are you?",
        ]
    }
}

def generate_seed_dataset():
    """Generate initial training dataset"""

    # Ensure output directory exists
    output_dir = Path(__file__).parent.parent / 'app' / 'ml_models' / 'training_data'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'coaching_messages.jsonl'

    examples = []

    for personality, risk_levels in SEED_MESSAGES.items():
        for risk_level, messages in risk_levels.items():
            for message in messages:
                # Generate realistic user context based on risk level
                if risk_level == 'low':
                    streak = random.randint(7, 100)
                    days_since = round(random.uniform(0.1, 1.0), 1)
                    effectiveness = random.uniform(0.75, 0.95)

                elif risk_level == 'medium':
                    streak = random.randint(3, 50)
                    days_since = round(random.uniform(1.5, 3.5), 1)
                    effectiveness = random.uniform(0.45, 0.75)

                else:  # high
                    streak = random.randint(0, 30)
                    days_since = round(random.uniform(3.0, 7.0), 1)
                    effectiveness = random.uniform(0.25, 0.60)

                # Format message with actual values
                formatted_message = message.format(
                    streak=streak,
                    days=days_since
                )

                context = {
                    'current_streak': streak,
                    'days_since_last_write': days_since
                }

                example = CoachingExample(
                    personality=personality,
                    risk_level=risk_level,
                    user_context=context,
                    message=formatted_message,
                    effectiveness=effectiveness
                )

                examples.append(example.to_dict())

    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example) + '\n')

    print(f"✓ Generated {len(examples)} seed examples")
    print(f"✓ Saved to: {output_file}")

    # Print summary
    from collections import Counter
    personalities = Counter(ex['personality'] for ex in examples)
    risk_levels = Counter(ex['risk_level'] for ex in examples)

    print("\n=== Summary ===")
    print(f"Total examples: {len(examples)}")
    print("\nBy personality:")
    for p, count in sorted(personalities.items()):
        print(f"  {p}: {count}")
    print("\nBy risk level:")
    for r, count in sorted(risk_levels.items()):
        print(f"  {r}: {count}")

    return examples

if __name__ == '__main__':
    generate_seed_dataset()
