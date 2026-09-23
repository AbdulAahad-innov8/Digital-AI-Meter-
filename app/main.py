from pathlib import Path
from datetime import datetime
import csv, statistics
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
try:
    from sklearn.ensemble import IsolationForest
    SK=True
except Exception: SK=False
BASE=Path(__file__).resolve().parent.parent; DATA=BASE/'data'/'meter_data.csv'; STATIC=BASE/'app'/'static'
app=FastAPI(title='Digital AI Meter',version='1.0.0')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
def load(resource=None):
    with open(DATA,newline='') as f: d=list(csv.DictReader(f))
    if resource: d=[r for r in d if r['resource']==resource]
    for r in d: r['consumption']=float(r['consumption']); r['dt']=datetime.fromisoformat(r['timestamp'])
    return d
def anomalies(d):
    vals=[r['consumption'] for r in d]
    if len(vals)<10:return []
    if SK: labels=IsolationForest(contamination=.06,random_state=42).fit_predict([[x] for x in vals])
    else:
        m=statistics.mean(vals); s=statistics.pstdev(vals) or 1; labels=[-1 if abs(x-m)>2.7*s else 1 for x in vals]
    return [{'timestamp':r['timestamp'],'consumption':r['consumption'],'severity':'high' if r['consumption']>statistics.mean(vals)*2.2 else 'medium'} for r,l in zip(d,labels) if l==-1]
def insight(resource,d,a):
    label='electricity' if resource=='electricity' else 'water'; vals=[r['consumption'] for r in d]; avg=sum(vals)/len(vals); recent=sum(vals[-6:])/6
    if a:
        x=a[-1]
        return (f'Unusual water usage was detected around {x["timestamp"]}. Continuous overnight usage may indicate a possible leakage pattern. Check taps, tanks and connected lines.' if resource=='water' else f'An unusual electricity spike was detected around {x["timestamp"]}. Check high-load appliances and equipment for unexpected usage.')
    return f'Recent {label} consumption is above the historical average. Consider checking the latest time slots and reducing avoidable usage.' if recent>avg*1.15 else f'{label.capitalize()} consumption is broadly within its recent range. Keep monitoring peak time slots for unusual changes.'
@app.get('/')
def home(): return FileResponse(STATIC/'index.html')
@app.get('/health')
def health(): return {'status':'ok','model':'Isolation Forest' if SK else 'statistical fallback'}
@app.get('/meter-data')
def meter_data(resource:str=Query('electricity')): return [{'timestamp':r['timestamp'],'consumption':r['consumption']} for r in load(resource)]
@app.get('/summary')
def summary(resource:str=Query('electricity')):
    d=load(resource); v=[r['consumption'] for r in d]; return {'resource':resource,'current':round(v[-1],2),'average':round(sum(v)/len(v),2),'peak':round(max(v),2),'last_24_total':round(sum(v[-24:]),2),'anomaly_count':len(anomalies(d)),'unit':'kWh' if resource=='electricity' else 'L'}
@app.get('/anomalies')
def get_anomalies(resource:str=Query('electricity')): return anomalies(load(resource))
@app.get('/prediction')
def prediction(resource:str=Query('electricity')):
    d=load(resource); v=[r['consumption'] for r in d[-12:]]; base=sum(v)/len(v); slope=(v[-1]-v[0])/max(1,len(v)-1); last=d[-1]['dt']
    return [{'timestamp':last.isoformat(),'predicted':round(max(0,base+slope*(i+1)),2)} for i in range(6)]
@app.get('/ai-insight')
def ai_insight(resource:str=Query('electricity')):
    d=load(resource); a=anomalies(d); return {'insight':insight(resource,d,a)}

@app.get('/ask-ai')
def ask_ai(question: str, resource: str = Query('electricity')):
    d = load(resource)
    a = anomalies(d)
    label = resource
    q = question.lower()
    u = 'kWh' if resource == 'electricity' else 'L'

    current = d[-1]['consumption']
    average = sum(r['consumption'] for r in d) / len(d)
    peak = max(d, key=lambda r: r['consumption'])
    last_24 = sum(r['consumption'] for r in d[-24:])

    if any(x in q for x in ['peak', 'highest', 'maximum']):
        return {
            'answer': f'The highest recorded {label} usage was {peak["consumption"]:.2f} {u} at {peak["timestamp"]}.'
        }

    if any(x in q for x in ['average', 'normal', 'usual']):
        return {
            'answer': f'The average {label} consumption is {average:.2f} {u} per hourly reading.'
        }

    if any(x in q for x in ['current', 'now', 'right now']):
        return {
            'answer': f'Your current {label} usage is {current:.2f} {u} per hour.'
        }

    if any(x in q for x in ['24', 'today', 'daily', 'last day']):
        return {
            'answer': f'Total recorded {label} consumption across the latest 24 hourly readings is {last_24:.2f} {u}.'
        }

    if any(x in q for x in ['anomal', 'unusual', 'abnormal', 'alert', 'spike']):
        if a:
            x = a[-1]
            return {
                'answer': f'I detected {len(a)} unusual {label} reading(s). The latest was {x["consumption"]:.2f} {u} at {x["timestamp"]}.'
            }
        return {
            'answer': f'No unusual {label} patterns were detected in the available readings.'
        }

    if any(x in q for x in ['saving', 'reduce', 'lower', 'waste']):
        if current > average * 1.15:
            return {
                'answer': f'Current {label} usage is above the historical average. Consider checking high-consumption appliances or recent time slots and reducing avoidable usage.'
            }
        return {
            'answer': f'Current {label} usage is within the recent range. Continue monitoring peak time slots to identify opportunities for saving.'
        }

    return {
        'answer': insight(resource, d, a)
    }

app.mount('/static',StaticFiles(directory=STATIC),name='static')
