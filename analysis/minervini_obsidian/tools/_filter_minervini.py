"""
Filter IRFC buy points by Minervini criteria from the RMV-GUIDED output
"""
import re
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(script_dir, 'IRFC_full_output.txt'), 'r', encoding='utf-8') as f:
    content = f.read()

s = content.find('RMV-GUIDED')
e = content.find('TIGHT STREAKS WITHOUT')
section = content[s:e]

entries = []
lines = section.split('\n')
i = 0
while i < len(lines) - 1:
    l = lines[i].strip()
    if not l.startswith('* Streak'):
        i += 1
        continue
    next_l = lines[i+1].strip()
    if not next_l.startswith('->'):
        i += 1
        continue
    streak_part = l
    entry_part = next_l[2:].strip()
    streak_match = re.search(r'Streak #(\d+) ended (\d{4}-\d{2}-\d{2}) \(avg RMV ([\d.]+)', streak_part)
    if not streak_match:
        i += 1
        continue
    i += 2
    streak_num = int(streak_match.group(1))
    streak_end = streak_match.group(2)
    avg_rmv = float(streak_match.group(3))
    entry_match = re.search(r'(\d+)d later: (.*?) @ (\d{4}-\d{2}-\d{2}) ([?]?[\d.]+) \([+]([\d.]+)%', entry_part)
    if not entry_match:
        continue
    days_later = int(entry_match.group(1))
    signal_type = entry_match.group(2)
    entry_date = entry_match.group(3)
    entry_price = entry_match.group(4).lstrip('?')
    gain_pct = float(entry_match.group(5))
    vr_match = re.search(r'VR ([\d.]+)x', entry_part)
    vr = float(vr_match.group(1)) if vr_match else 0

    score = 0
    tags = []
    if avg_rmv <= 5:
        score += 3
        tags.append('elite-tight')
    elif avg_rmv <= 8:
        score += 2
        tags.append('strong-tight')
    elif avg_rmv <= 12:
        score += 1
        tags.append('moderate-tight')
    if days_later <= 3:
        score += 2
        tags.append('immediate')
    elif days_later <= 7:
        score += 1
        tags.append('quick')
    if vr >= 5.0:
        score += 3
        tags.append('massive-vol')
    elif vr >= 2.5:
        score += 2
        tags.append('strong-vol')
    elif vr >= 1.5:
        score += 1
        tags.append('adequate-vol')
    if 'PIVOT-B/O' in signal_type:
        score += 3
        tags.append('pivot-bo')
    elif 'BO(v' in signal_type:
        score += 2
        tags.append('breakout')
    if gain_pct >= 5:
        score += 1
        tags.append('big-day')

    entries.append({
        'streak_num': streak_num, 'avg_rmv': avg_rmv, 'streak_end': streak_end,
        'days_later': days_later, 'signal_type': signal_type, 'entry_date': entry_date,
        'entry_price': entry_price, 'gain_pct': gain_pct, 'vr': vr, 'score': score,
        'tags': ' | '.join(tags)
    })

entries.sort(key=lambda x: x['score'], reverse=True)

outpath = os.path.join(script_dir, 'IRFC_minervini_buys.txt')
with open(outpath, 'w', encoding='utf-8') as out:
    out.write('=' * 110 + '\n')
    out.write('  IRFC: MINERVINI HIGH-PROBABILITY BUY POINTS (Ranked)\n')
    out.write('=' * 110 + '\n\n')
    out.write(f"{'#':<4} {'DATE':<12} {'PRICE':<10} {'RMV':<6} {'VR':<7} {'DAYS':<6} {'GAIN%':<8} {'SIGNAL':<22} {'MINERVINI TAGS'}\n")
    out.write('-' * 110 + '\n')
    rank = 0
    for e in entries:
        rank += 1
        out.write(f"#{rank:<3} {e['entry_date']:<12} Rs{e['entry_price']:<7} {e['avg_rmv']:<4.1f}  {e['vr']:<4.1f}x  {e['days_later']:<4}d +{e['gain_pct']:<5.1f}%  {e['signal_type']:<22} {e['tags']}\n")

    out.write('\n' + '=' * 110 + '\n')
    out.write('  ELITE MINERVINI ENTRIES (Score >= 8)\n')
    out.write('=' * 110 + '\n')
    for e in entries:
        if e['score'] >= 8:
            out.write(f"\n>>> BUY: Rs{e['entry_price']} on {e['entry_date']}\n")
            out.write(f"    Streak #{e['streak_num']} ended {e['streak_end']} (RMV {e['avg_rmv']:.1f})\n")
            out.write(f"    {e['days_later']} days later: {e['signal_type']} [+{e['gain_pct']}%, VR {e['vr']}x]\n")
            out.write(f"    Tags: {e['tags']}\n")

    rejected = [e for e in entries if e['score'] < 5]
    out.write(f"\n  Rejected: {len(rejected)} entries filtered out (score < 5)\n")

    # Add legend
    out.write("\n\n" + "=" * 110 + "\n")
    out.write("  MINERVINI CLASSIFICATION LEGEND\n")
    out.write("=" * 110 + "\n")
    out.write("  Scoring (max 12):\n")
    out.write("  - Tightness: elite(0-5RMV=3) | strong(5-8RMV=2) | moderate(8-12RMV=1)\n")
    out.write("  - Timing: immediate(0-3d=2) | quick(4-7d=1)\n")
    out.write("  - Volume: massive(5.0x+=3) | strong(2.5x+=2) | adequate(1.5x+=1)\n")
    out.write("  - Signal: pivot-bo(+3) | breakout(+2)\n")
    out.write("  - Big day(>=5%+1)\n")
    out.write("\n  Score >= 8: Elite Minervini entry (tightness + volume + pivot-clearing)\n")
    out.write("  Score 6-7: Good entry\n")
    out.write("  Score 5: Marginal\n")
    out.write("  Score < 5: Avoid\n")

print(f"Done! Written to {outpath}")
