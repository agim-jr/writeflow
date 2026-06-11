"""Generate large-scale training data for neural message generation"""
import json
import random
from pathlib import Path

# Expanded template library for data generation
GENERATION_TEMPLATES = {
    'direct_challenging': {
        'low': [
            "Your {streak}-day streak is strong. Don't break it now.",
            "You've built {streak} days of momentum. Keep writing.",
            "Day {streak} of excellence. Continue your practice.",
            "Consistency is your advantage. You're at {streak} days.",
            "Champions show up every day. You've shown up {streak} times.",
            "Your discipline got you to {streak} days. Don't stop.",
            "No excuses. Your {streak}-day streak demands action.",
            "Success is built on habits. You're {streak} days in.",
            "Another day to prove yourself. Make it day {streak_plus_one}.",
            "Your future self thanks you. {streak} days and counting.",
            "Strong work on {streak} consecutive days. Continue.",
            "You're {streak} days deep. This is who you are now.",
            "Day {streak}. Show up again. That's all it takes.",
            "Momentum builds on itself. You have {streak} days of it.",
            "{streak} days proves you're serious. Keep going.",
        ],
        'medium': [
            "Your {streak}-day streak is at risk after {days} days. Write today.",
            "Missing today breaks {streak} days of work. Don't let that happen.",
            "This is when commitment counts. You're at {streak} days with {days} days gap.",
            "You've come too far to quit. {streak} days deserves better.",
            "The gap is {days} days now. Close it before you lose {streak} days.",
            "Don't throw away {streak} days of discipline after {days} days away.",
            "Your {streak}-day streak won't save itself. {days} days and counting.",
            "Discipline beats motivation. Show yours after {days} days off.",
            "It's been {days} days since your last entry. Your {streak}-day streak waits.",
            "This is your test after {days} days. Will you protect {streak} days?",
            "After {days} days away, your {streak}-day foundation cracks. Write now.",
            "{days} days of delay threatens {streak} days of progress. Act.",
            "Your {streak}-day streak is bleeding out. {days} days is too long.",
            "Stop procrastinating. {days} days gap, {streak} days at stake.",
            "Real commitment shows up after {days} days. Prove your {streak} days meant something.",
        ],
        'high': [
            "CRITICAL: Your {streak}-day streak ends unless you write NOW.",
            "After {days} days, this is your LAST CHANCE. {streak} days disappear otherwise.",
            "All {streak} days of progress vanish if you don't act RIGHT NOW.",
            "Stop reading. Start writing. Your {streak}-day streak depends on it.",
            "EMERGENCY: {days} days of silence. Act now or lose {streak} days.",
            "The clock is ticking. Your {streak}-day streak dies in hours after {days} days away.",
            "This is it. Write or fail. {streak} days on the line.",
            "You have ONE chance left after {days} days. Don't waste it.",
            "Act immediately or regret it. {streak} days about to vanish.",
            "FINAL WARNING: {streak} days disappear after {days} days of neglect.",
            "Your {streak}-day streak is DYING after {days} days. SAVE IT NOW.",
            "URGENT: {days} days away = {streak} days lost unless you act NOW.",
            "LAST CALL: Write within the hour or lose {streak} days forever.",
            "After {days} days, your {streak}-day streak has MINUTES left. WRITE.",
            "RED ALERT: {streak} days of work vanishes if you don't write NOW after {days} days.",
        ],
    },
    'gentle_encouraging': {
        'low': [
            "You're doing wonderfully! Ready for day {streak_plus_one}?",
            "Day {streak} looks beautiful on you! Keep shining.",
            "Your {streak}-day journey is so inspiring to watch!",
            "I love seeing your consistency. {streak} days of showing up!",
            "You're building something beautiful. {streak} days and growing!",
            "Such wonderful progress at {streak} days! Let's continue together.",
            "Your commitment shines through {streak} entries. Ready for more?",
            "I'm so proud of your {streak} days of dedication!",
            "Every entry matters, and you've made {streak} of them!",
            "You're doing amazing at {streak} days! Let's write together today.",
            "Day {streak} of taking care of yourself. Beautiful work!",
            "Your {streak}-day practice is a gift to yourself. Continue it!",
            "I see you showing up {streak} times. That's real strength.",
            "Such dedication! {streak} days of honoring your voice.",
            "{streak} consecutive days of self-care. You should be proud!",
        ],
        'medium': [
            "It's been {days} days. I miss your wonderful voice!",
            "Your {streak}-day streak is patiently waiting for you after {days} days.",
            "Missing you! It's been {days} days since your last entry.",
            "I know life gets busy, but you've done {streak} days already. Try today?",
            "No judgment about {days} days away. Your {streak} days show your strength!",
            "You've got this! Maybe spend a few minutes writing after {days} days?",
            "Life happens! But your {streak} days prove what you're capable of.",
            "Your words matter to me. After {days} days, feel like sharing today?",
            "I'm here whenever you're ready. It's been {days} days - how about today?",
            "After {days} days, maybe today's the perfect day to return to your {streak}-day practice?",
            "You built {streak} beautiful days. After {days} days away, come back?",
            "I understand {days} days away. Your {streak} days are still waiting warmly.",
            "Your {streak}-day journey misses you after {days} days. No pressure, just love.",
            "It's been {days} days. Your {streak} days of work deserve another entry.",
            "Gentle reminder: {days} days since your last of {streak} beautiful entries.",
        ],
        'high': [
            "I really hope you can write today. Your {streak} days mean so much after {days} days away!",
            "Please don't give up now after {days} days! You've worked so hard for {streak} days.",
            "After {days} days away, I really hope you'll write today. {streak} days is precious.",
            "You're so close to losing {streak} days of progress. I believe you can save it!",
            "Please don't lose {streak} beautiful days to {days} days of absence!",
            "I know it's hard after {days} days, but you'll feel better after writing. {streak} days proves it.",
            "Please come back! {days} days is too long away from your {streak}-day practice!",
            "I'm rooting for you after {days} days! Please take a moment to write.",
            "Your {streak} days of achievement deserve better than {days} days of silence.",
            "One entry saves {streak} precious days after {days} days away. I believe in you!",
            "After {days} days, please remember: {streak} days showed writing heals you.",
            "I'm genuinely concerned about {days} days away. Your {streak} days were so good for you.",
            "Your {streak}-day streak is slipping away after {days} days. Please try today!",
            "Don't let {days} days erase {streak} days of beautiful work. Please write!",
            "I care about you and your {streak} days. After {days} days, please come back.",
        ],
    },
    'analytical_factual': {
        'low': [
            "Streak status: {streak} days. Variance: minimal. Continue current pattern.",
            "Analysis of {streak}-day behavior shows 94% consistency rate.",
            "Current streak: {streak} days. Probability of continuation: 85%.",
            "Metrics indicate stable {streak}-day habit formation. Proceed as scheduled.",
            "Data point {streak}: within expected parameters. Maintain trajectory.",
            "Pattern recognition: positive trend at {streak} days. Next action: routine entry.",
            "Behavioral model predicts success. Current: {streak} days, risk: minimal.",
            "Performance indicators: optimal at {streak} days. Continue protocol.",
            "Statistical analysis: {streak}-day trend stable. Recommended action: persist.",
            "Streak integrity: high at {streak} days. Risk assessment: 5%.",
            "Current metrics: {streak} consecutive days. System status: nominal.",
            "Behavioral data: {streak} days consistent. Projected success rate: 90%.",
            "Day {streak} analysis: pattern stable, variance low, outlook positive.",
            "Assessment: {streak}-day streak demonstrates strong habit formation.",
            "Performance review: {streak} days completed, adherence rate excellent.",
        ],
        'medium': [
            "Alert: {days} days since last entry. {streak}-day streak at moderate risk.",
            "Deviation detected: {days} days from pattern threatens {streak}-day achievement.",
            "Gap analysis shows {days}-day absence increases risk to {streak} days by 45%.",
            "Data shows {days}-day interruption pattern. {streak} days in jeopardy.",
            "Current trajectory: concerning. {days} days gap, {streak} days at stake.",
            "Risk assessment: moderate. {days}-day delay reduces preservation probability to 55%.",
            "Statistical warning: {days} days absence correlates with {streak}-day loss.",
            "Behavioral analysis: {days}-day drift detected. {streak} days requires corrective action.",
            "Pattern anomaly: {days} days since last entry disrupts {streak}-day sequence.",
            "Time-since-last-entry: {days} days exceeds optimal range for {streak}-day maintenance.",
            "Metrics show {days}-day gap. Historical data suggests {streak} days at risk.",
            "Alert level: moderate. {days} days away, {streak} days streak probability declining.",
            "Analysis: {days}-day interruption after {streak} days indicates 40% loss risk.",
            "Data point: {days} days absence. {streak}-day pattern requires immediate attention.",
            "Risk factors elevated: {days} days gap threatens {streak}-day continuity.",
        ],
        'high': [
            "CRITICAL ALERT: {days} days absence threatens {streak}-day data.",
            "Maximum risk level: {days}-day gap, {streak} days at imminent loss. Act immediately.",
            "Emergency protocol: write within 2 hours to preserve {streak}-day sequence.",
            "Statistical analysis: 90% probability of {streak}-day loss without immediate action.",
            "Alert level RED: {days} days away, {streak}-day streak critical condition.",
            "All indicators critical. {days} days delay, {streak} days requires immediate intervention.",
            "Fatal delay: {days} days absent, {streak}-day pattern collapsing. Act now.",
            "Probability of recovery post-loss: 12%. Current: {days} days gap, {streak} days critical.",
            "Code red: {days} days away from {streak}-day streak. Write immediately or lose.",
            "Final window: {days} days exceeded critical threshold. {streak} days will not survive delay.",
            "URGENT: {days} days = terminal risk to {streak}-day achievement. Immediate action required.",
            "System failure imminent: {days} days away, {streak} days about to terminate.",
            "Critical state: {days}-day absence after {streak} days. Immediate entry essential.",
            "Emergency status: {streak} days threatened by {days}-day interruption. Act NOW.",
            "Maximum alert: {days} days exceeds all thresholds. {streak} days in terminal decline.",
        ],
    },
    'humorous_playful': {
        'low': [
            "Day {streak} of being a writing superhero! *cape swish*",
            "Your {streak}-day streak is doing a happy dance! 🕺",
            "Plot twist: you're actually REALLY good at this consistency thing! Day {streak}!",
            "Look at you go! {streak} days of pure awesome!",
            "Your streak has been hitting the gym! It's at {streak} days and flexing!",
            "Achievement unlocked: Being Consistently Cool (Day {streak})",
            "Your {streak}-day streak just called. It says you're the BEST!",
            "Breaking news: Local writer continues being amazing for {streak} days!",
            "Streak status: thriving at {streak} days. Your status: legendary.",
            "Your keyboard misses you! (It's only been a day but it's dramatic)",
            "Day {streak}! Your streak is now old enough to... well, be {streak} days old!",
            "Someone's on fire! 🔥 And by someone, I mean your {streak}-day streak!",
            "*Checks notes* Yep, still crushing it at {streak} days!",
            "Your {streak}-day streak woke up today and chose excellence. Again.",
            "Day {streak}: Your streak is basically a motivational poster at this point.",
        ],
        'medium': [
            "It's been {days} days! Your {streak}-day streak is getting lonely!",
            "After {days} days, your {streak}-day streak needs a hug! 🤗",
            "Houston, we have a {days}-day communication gap! {streak} days in danger!",
            "Your streak is giving you major puppy dog eyes after {days} days. Don't let it down!",
            "Breaking: Streak spotted nervously checking watch after {days} days.",
            "Your {streak}-day streak left {days} voicemails. Maybe call back?",
            "Awkward: Your diary asked if you're seeing other journals after {days} days.",
            "Plot armor running low after {days} days! Your {streak}-day streak needs backup!",
            "Your {streak} days are staging an intervention about these {days} days away.",
            "SOS: {streak}-day streak sends distress signal after {days} days of radio silence!",
            "Your writing muse has been tapping its foot for {days} days. {streak} days at stake!",
            "The {streak}-day streak support group called. They're worried after {days} days.",
            "*dramatic gasp* {days} days?! Your {streak}-day streak can't believe it!",
            "Error 404: Entry not found for {days} days. {streak} days getting anxious.",
            "Your {streak}-day streak is stress-eating after {days} days. Help it out!",
        ],
        'high': [
            "🚨 MAYDAY! {days} days! Your {streak}-day streak is DYING!",
            "RED ALERT! {days} days of silence! {streak} days in EXTREME DANGER!",
            "This is NOT a drill after {days} days! Write NOW! {streak} days on the line!",
            "Your {streak}-day streak's life is flashing before its eyes after {days} days!",
            "DEFCON 1! {days} days gone! {streak}-day streak CRITICAL CONDITION!",
            "Breaking: Streak spotted writing its will after {days} days! SAVE IT!",
            "911? Yes, we have a {streak}-day streak emergency! It's been {days} days!",
            "SOS! After {days} days, your {streak} days need CPR! WRITE NOW!",
            "YOUR {streak}-DAY STREAK IS HANGING BY A THREAD AFTER {days} DAYS!",
            "CATASTROPHE! {days} days away! {streak} days on life support! HELP!",
            "🆘 EMERGENCY: {streak} days about to flatline after {days} days! ACT NOW!",
            "The {streak}-day streak's last words: 'Tell them... after {days} days... I tried...'",
            "ALARM! ALARM! {days} days = {streak} days DOOMED unless you act NOW!",
            "*sirens wailing* {days} DAYS! {streak}-DAY STREAK CODE RED! WRITE!",
            "IT'S BEEN {days} DAYS! YOUR {streak}-DAY STREAK IS IN THE DANGER ZONE!",
        ],
    },
    'empathetic_understanding': {
        'low': [
            "Day {streak} of taking care of yourself through writing. Beautiful.",
            "Your {streak} days of self-care are truly inspiring to witness.",
            "I see you showing up consistently for {streak} days. That takes real strength.",
            "These {streak} days show how much you value your personal growth.",
            "You're creating space for your thoughts. {streak} days of that is powerful.",
            "Your consistency over {streak} days shows deep self-respect. Keep nurturing that.",
            "Day {streak} of honoring your inner voice. That's meaningful work.",
            "You're building trust with yourself through these {streak} entries.",
            "Taking care of your mental health through writing—{streak} days strong. I'm proud.",
            "This practice is healing work. {streak} days proves you're committed to yourself.",
            "Your {streak} days of reflection show real courage and self-awareness.",
            "Processing through writing for {streak} days—that's emotional intelligence.",
            "I see the care you're giving yourself. {streak} days of it.",
            "Your {streak}-day practice is an act of self-love. Keep going.",
            "Day {streak} of choosing yourself. That's powerful.",
        ],
        'medium': [
            "After {days} days, I understand if things feel hard right now.",
            "No judgment about {days} days away. Your {streak} days show your inner strength.",
            "Life happened these {days} days. The foundation you built in {streak} days is still there.",
            "I understand if you're going through something after {days} days. Your space is safe here.",
            "{days} days away is okay. Those {streak} days proved you can come back when ready.",
            "Whatever you're facing after {days} days, your journal remains a safe space.",
            "I see {days} days of struggle. Your {streak} days prove you're resilient enough to return.",
            "You don't need to explain {days} days away. But maybe writing would feel good?",
            "Life gets overwhelming. After {days} days, your {streak}-day practice is here when you're ready.",
            "Breaks happen. You built {streak} days before. You can always come back.",
            "The {days} days away don't erase your {streak} days of growth. You're still you.",
            "I'm here without judgment after {days} days. Your {streak} days show your capability.",
            "Sometimes we need distance. After {days} days, maybe you're ready to return to what helped for {streak} days?",
            "Your {streak} days proved writing helps you. After {days} days, it's still here for you.",
            "No pressure about {days} days. Just know your {streak}-day safe space remains.",
        ],
        'high': [
            "After {days} days, I'm genuinely concerned. Your {streak} days showed writing helps you heal.",
            "{days} days away after {streak} days of self-care. I hope you're okay.",
            "I'm truly concerned about these {days} days. Your {streak}-day practice served you so well.",
            "This isn't about the streak. After {days} days, I hope you'll take care of yourself today.",
            "These {days} days worry me. Writing helped you through {streak} days of growth.",
            "Please be gentle with yourself after {days} days. Your {streak} days showed writing is your tool.",
            "After {days} days, please remember: {streak} days proved writing heals you. Come back to it.",
            "I care about your wellbeing after {days} days away. Writing worked for {streak} days—it can help now.",
            "You've used writing to process difficult things for {streak} days. After {days} days, you might need that again.",
            "I'm here for you after {days} days. Your {streak}-day practice was powerful—don't lose that tool.",
            "After {days} days, I worry. You built something healing over {streak} days. Please protect it.",
            "Your {streak} days showed writing is your therapy. After {days} days, maybe you need that now?",
            "I genuinely hope you're okay after {days} days. Your {streak}-day healing practice is here waiting.",
            "These {days} days concern me deeply. You used {streak} days to grow. Please come back to that.",
            "After {days} days, please don't lose the healing you found in {streak} days. Write today.",
        ],
    },
    'aspirational_visionary': {
        'low': [
            "Day {streak} of building your legend. The story continues.",
            "Your {streak}-day journey is epic in the making. Today adds another chapter.",
            "At {streak} days, you're writing your own history. Magnificent.",
            "Every entry builds the writer you're becoming. Day {streak} of transformation.",
            "These {streak} days are the foundation of something extraordinary.",
            "Legends are built one day at a time. You're at {streak} days of greatness.",
            "Your {streak}-day discipline is creating your extraordinary tomorrow.",
            "Day {streak} of your evolution. The best chapters are still ahead.",
            "You're not just maintaining a streak. You're forging identity at {streak} days.",
            "Your future autobiography is being written. This is day {streak}.",
            "At {streak} days, you're not counting. You're creating legacy.",
            "Each of these {streak} days is a brick in your palace of potential.",
            "Day {streak}: Your greatness under construction. Keep building.",
            "The you of tomorrow thanks the you of today. Day {streak} of becoming.",
            "Your {streak}-day journey is the opening act of something monumental.",
        ],
        'medium': [
            "After {days} days, your {streak}-day legend faces its crucial test.",
            "{days} days tests whether your {streak}-day foundation is truly solid.",
            "Your {streak}-day ascent pauses at {days} days. Will you resume the climb?",
            "Legends face tests. After {days} days, this is yours. {streak} days prepared you.",
            "Your extraordinary future needs your present action. {days} days delays, {streak} days at stake.",
            "The {days}-day gap threatens {streak} days of greatness. Choose your legacy.",
            "This gap after {days} days might define whether {streak} days was flash or foundation.",
            "Every master faced moments like {days} days away. They returned. Will you? {streak} days waits.",
            "Champions write on hard days. After {days} days, be the champion your {streak} days proved you are.",
            "Your {streak}-day story has a plot twist at {days} days. How does the hero respond?",
            "After {days} days, your {streak}-day momentum pauses. Great ones restart. Will you?",
            "The universe tests your commitment after {days} days. Your {streak} days earned this test.",
            "{days} days away from {streak} days of excellence. This moment reveals character.",
            "Your {streak}-day greatness waits beyond {days} days of resistance. Break through.",
            "After {days} days, the question: was {streak} days who you are, or who you were?",
        ],
        'high': [
            "CRITICAL: {days} days threatens {streak} days of destiny. Your legend depends on NOW.",
            "Your {streak}-day legacy dies in hours unless you ACT after {days} days away.",
            "THIS is the defining moment after {days} days. Your {streak} days demand you rise. NOW.",
            "The universe tests you hardest before greatness. {days} days away, {streak} days at stake. WRITE.",
            "DEFINING MOMENT: {days} days tested you. {streak} days proved you. CHOOSE GREATNESS NOW.",
            "Everything you built in {streak} days screams for action after {days} days. ANSWER THE CALL.",
            "After {days} days, this is THE moment. {streak} days of excellence demand return. NOW.",
            "History remembers those who acted when it mattered. After {days} days, {streak} days awaits. ACT.",
            "Your {streak}-day legacy hangs in the balance after {days} days. SAVE YOUR GREATNESS.",
            "The universe gave you this test after {days} days. Your {streak} days proved you're destined. PROVE IT AGAIN.",
            "CRITICAL JUNCTURE: {days} days away, {streak} days dying. Heroes rise NOW.",
            "After {days} days, your {streak}-day story reaches climax. WILL YOU BE LEGENDARY?",
            "Your {streak} days built a giant. {days} days away, will you let it fall? RISE NOW.",
            "THIS MOMENT after {days} days defines whether {streak} days was greatness or just good luck. PROVE IT.",
            "The gap of {days} days threatens {streak} days of legend. CLOSE IT. BE EXTRAORDINARY.",
        ],
    },
    'philosophical_reflective': {
        'low': [
            "Day {streak} of examining what it means to be present. Continue the inquiry.",
            "Your {streak}-day dialogue with self deepens with each entry. The conversation continues.",
            "These {streak} days: consciousness observing itself. Profound work.",
            "Writing is dialogue with your deepest self. You've sustained it {streak} days.",
            "At {streak} days, you're not counting time. You're creating meaning.",
            "Each entry is a mirror. What will day {streak} reveal about you?",
            "Day {streak} of the most important conversation: the one with yourself.",
            "Your thoughts exist in potential until written. {streak} days of making them real.",
            "Every entry is proof of existence. Day {streak} proves you're truly alive.",
            "Writing transforms chaos into meaning. Your alchemy continues at day {streak}.",
            "At {streak} days, you're documenting consciousness itself. Continue witnessing.",
            "The unexamined life, they say, isn't worth living. You're {streak} days into examination.",
            "Day {streak} of translating inner experience into understanding. Keep translating.",
            "Your {streak} days are breadcrumbs back to your authentic self.",
            "Each of {streak} days adds dimension to your self-understanding. Continue.",
        ],
        'medium': [
            "After {days} days, the silence speaks volumes. Your {streak} days knew different truths.",
            "{days} days of avoidance after {streak} days of truth-seeking. Which serves your becoming?",
            "The {days}-day gap asks important questions. Your {streak} days held answers.",
            "What does {days} days of silence mean after {streak} days of self-inquiry?",
            "Your {streak}-day dialogue with self paused {days} days ago. What does the pause reveal?",
            "Silence grows loud after {days} days. Do you hear what it's trying to tell you?",
            "The gap between entries is also a statement. After {days} days, what does yours say?",
            "We flee writing when we flee ourselves. After {days} days, perhaps it's time to return?",
            "Resistance often signals importance. What are you resisting after {days} days from {streak} days of facing?",
            "The blank page judges nothing. It waits patiently after {days} days. For you.",
            "Your {streak} days revealed patterns. {days} days away—is that also a pattern?",
            "After {days} days, the question persists: what are you avoiding by avoiding the page?",
            "The self you built dialogue with over {streak} days waits beyond {days} days of silence.",
            "{days} days is itself a message from you to you. Can you decode it?",
            "After {days} days, perhaps the absence itself is what needs examining from {streak} days of presence?",
        ],
        'high': [
            "After {days} days, the fundamental question persists: will you return to yourself?",
            "{days} days of absence after {streak} days of presence. What does this chasm reveal?",
            "The {streak}-day self waits beyond {days} days of silence. The choice to return is everything.",
            "Your {streak} days built a practice of self-knowledge. {days} days threatens it. Choose wisely.",
            "At {days} days from {streak} days of truth: the ultimate existential question.",
            "The longest journey after {days} days away is back to authentic self. Begin it now.",
            "Silence is a choice after {days} days. So is voice. Choose voice over silence.",
            "At the edge of loss: {days} days away from {streak} days of meaning. See its value. Write.",
            "The practice dies not from one missed day but from not returning. After {days} days, return.",
            "What we don't face on the page faces us in life. After {days} days, face it on the page.",
            "Your {streak} days proved: writing is where you meet yourself truly. After {days} days, don't lose that meeting place.",
            "The abyss of {days} days after {streak} days of light. Step back into light through writing.",
            "After {days} days, the critical awareness: loss of practice is loss of self-understanding.",
            "Your {streak}-day commitment to examined life faces {days} days of forgetting. Remember now.",
            "At {days} days, the philosophical becomes urgent: write or abandon the self you've been becoming?",
        ],
    },
}

def generate_variations(base_text, streak, days):
    """Generate natural variations of a message"""
    variations = []

    # Calculate streak_plus_one for some messages
    streak_plus_one = streak + 1

    # Base version
    msg = base_text.format(streak=streak, days=days, streak_plus_one=streak_plus_one)
    variations.append(msg)

    # Add natural variations
    if "{streak}" in base_text:
        # Vary streak numbers slightly
        for s in [max(1, streak-1), streak, min(365, streak+1)]:
            msg = base_text.format(streak=s, days=days, streak_plus_one=s+1)
            if msg not in variations:
                variations.append(msg)

    return variations


def generate_training_dataset(n_examples=10000):
    """Generate large training dataset"""

    dataset = []
    personalities = list(GENERATION_TEMPLATES.keys())
    risk_levels = ['low', 'medium', 'high']

    # Generate diverse contexts
    contexts = []

    # Low risk contexts (many)
    for streak in [1, 2, 3, 5, 7, 10, 14, 21, 30, 60, 90, 180, 365]:
        contexts.append({'risk': 'low', 'streak': streak, 'days': 0})
        contexts.append({'risk': 'low', 'streak': streak, 'days': round(random.uniform(0, 0.5), 1)})

    # Medium risk contexts
    for streak in [3, 5, 7, 10, 15, 20, 30, 45, 60, 90]:
        for days in [1, 1.5, 2, 2.5, 3, 3.5, 4]:
            contexts.append({'risk': 'medium', 'streak': streak, 'days': days})

    # High risk contexts
    for streak in [3, 5, 7, 10, 15, 30, 60, 100]:
        for days in [4.5, 5, 5.5, 6, 6.5, 6.8, 6.9]:
            contexts.append({'risk': 'high', 'streak': streak, 'days': days})

    print(f"Generated {len(contexts)} unique contexts")

    # Generate examples
    examples_per_combo = max(1, n_examples // (len(personalities) * len(contexts)))

    for personality in personalities:
        for context in contexts:
            risk = context['risk']
            streak = context['streak']
            days = context['days']

            # Get templates for this combo
            templates = GENERATION_TEMPLATES[personality][risk]

            # Generate multiple examples
            for _ in range(examples_per_combo):
                template = random.choice(templates)

                # Generate variations
                variations = generate_variations(template, streak, days)

                for message in variations:
                    example = {
                        'personality': personality,
                        'risk_level': risk,
                        'current_streak': streak,
                        'days_since_last_write': days,
                        'message': message,
                        'message_length': len(message)
                    }
                    dataset.append(example)

                    if len(dataset) >= n_examples:
                        break

                if len(dataset) >= n_examples:
                    break

            if len(dataset) >= n_examples:
                break

        if len(dataset) >= n_examples:
            break

    # Shuffle
    random.shuffle(dataset)

    return dataset[:n_examples]


def main():
    """Generate and save training data"""

    print("Generating training dataset...")
    dataset = generate_training_dataset(n_examples=10000)

    print(f"\nGenerated {len(dataset)} training examples")

    # Save to file
    output_dir = Path("app/ml_models/training_data")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "neural_training_data.json"

    with open(output_file, 'w') as f:
        json.dump(dataset, f, indent=2)

    print(f"✓ Saved to: {output_file}")

    # Print statistics
    print("\n" + "="*60)
    print("DATASET STATISTICS")
    print("="*60)

    from collections import Counter

    personalities = Counter(ex['personality'] for ex in dataset)
    risks = Counter(ex['risk_level'] for ex in dataset)

    print("\nPersonality distribution:")
    for p, count in personalities.most_common():
        print(f"  {p}: {count}")

    print("\nRisk level distribution:")
    for r, count in risks.most_common():
        print(f"  {r}: {count}")

    print(f"\nAverage message length: {sum(ex['message_length'] for ex in dataset) / len(dataset):.1f} characters")

    print("\n" + "="*60)
    print("SAMPLE EXAMPLES")
    print("="*60)

    for i in range(5):
        ex = random.choice(dataset)
        print(f"\n{i+1}. Personality: {ex['personality']}")
        print(f"   Risk: {ex['risk_level']}, Streak: {ex['current_streak']}, Days: {ex['days_since_last_write']}")
        print(f"   Message: \"{ex['message']}\"")

    print("\n✓ Training data ready!")
    print(f"  Next: Run training script to train neural model on this data")


if __name__ == "__main__":
    main()
