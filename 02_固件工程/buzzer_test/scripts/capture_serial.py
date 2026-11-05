"""Record the test firmware's runtime messages without resetting the board."""
import json,time
from pathlib import Path
import serial
project=Path(__file__).resolve().parent.parent
records=[]
started=time.monotonic()
with serial.Serial('COM3',115200,timeout=0.25) as port:
    while time.monotonic()-started<7:
        line=port.readline().decode('utf-8',errors='replace').strip()
        if line:records.append({'elapsed_s':round(time.monotonic()-started,3),'line':line})
on=sum(r['line']=='BUZZER ON' for r in records)
off=sum(r['line']=='BUZZER OFF' for r in records)
report={'port':'COM3','baud':115200,'on_messages':on,'off_messages':off,'records':records,'runtime_confirmed':on>=2 and off>=2,'audible_sound_not_measured':True}
(project/'logs'/'runtime-serial.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=True))
if not report['runtime_confirmed']:raise SystemExit(1)
