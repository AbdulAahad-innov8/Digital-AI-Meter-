let r = 'electricity';

const $ = (x) => document.getElementById(x);
const unit = () => (r === 'electricity' ? 'kWh' : 'L');

async function get(x) {
  return (await fetch(x)).json();
}

async function load(){
    let [s,d,an,i,rec] = await Promise.all([
        get('/summary?resource='+r),
        get('/meter-data?resource='+r),
        get('/anomalies?resource='+r),
        get('/ai-insight?resource='+r),
        get('/recommendation?resource='+r)
    ]);

    $('cur').textContent=s.current.toFixed(2);
    $('avg').textContent=s.average.toFixed(2);
    $('peak').textContent=s.peak.toFixed(2);
    $('ac').textContent=an.length;
    $('u').textContent=unit()+' / hour';

    $('insight').textContent=i.insight;
    $('recommendation').textContent=rec.recommendation;

    chart(d);
    alerts(an);
    slots(d);
}

function predictions(p){
    $('prediction').innerHTML = p.map((x,i) => `
        <div class="prediction-item">
            <span>+${i+1} hr</span>
            <b>${x.predicted.toFixed(2)} ${unit()}</b>
        </div>
    `).join('');
}


function chart(d,pred=[]){
    let v=d.map(x=>+x.consumption);
    let pv=pred.map(x=>+x.predicted);

    let W=900,H=300,p=20;
    let all=[...v,...pv];
    let M=Math.max(...all)*1.08;

    let historical=v.map((x,i)=>[
        p+i*(W-2*p)/(v.length+pred.length-1),
        H-p-x/M*(H-2*p)
    ]);

    let predicted=pv.map((x,i)=>[
    p+(v.length-1+i)*(W-2*p)/(v.length+pred.length-1),
        H-p-x/M*(H-2*p)
    ]);

    let historicalPath=historical
        .map((q,i)=>(i?'L':'M')+q[0]+' '+q[1])
        .join(' ');

    let predictedPath=predicted.length
        ? 'M'+historical[historical.length-1][0]+' '+historical[historical.length-1][1]+' '+
          predicted.map(q=>'L'+q[0]+' '+q[1]).join(' ')
        : '';

    let svg=document.querySelector('#chart svg');

    svg.innerHTML=
        '<path d="M20 280 H880" stroke="#edf0f5"/>'+
        '<path d="'+historicalPath+'" fill="none" stroke="#3277df" stroke-width="3" stroke-linecap="round"/>'+
        '<path d="'+predictedPath+'" fill="none" stroke="#3277df" stroke-width="3" stroke-dasharray="8 6"/>'
}

function alerts(a) {
  $('alerts').innerHTML =
    a.slice(-5).reverse().map((x) => `
      <div class="al">
        <b>⚠ Unusual ${r} usage</b><br>
        <small>${new Date(x.timestamp).toLocaleString()} • ${x.consumption} ${unit()} • ${x.severity} priority</small>
      </div>
    `).join('') || '<div class="answer">No unusual patterns detected.</div>';
}

function slots(d) {
  let b = [[], [], [], []];

  d.forEach((x) => {
    let h = new Date(x.timestamp).getHours();
    let index = h < 6 ? 0 : h < 12 ? 1 : h < 18 ? 2 : 3;
    b[index].push(Number(x.consumption));
  });

  ['n', 'm', 'a', 'ev'].forEach((id, i) => {
    let average = b[i].length
      ? b[i].reduce((sum, x) => sum + x, 0) / b[i].length
      : 0;
    $(id).textContent = average.toFixed(2) + ' ' + unit();
  });
}

$('e').onclick=()=>{
    r='electricity';
    $('e').classList.add('active');
    $('w').classList.remove('active');
    load();
    loadRecommendation();
};

$('w').onclick=()=>{
    r='water';
    $('w').classList.add('active');
    $('e').classList.remove('active');
    load();
    loadRecommendation();
};

$('ask').onclick = async () => {
  $('answer').textContent = 'Analyzing…';
  let q = $('q').value || 'Why did my usage spike?';
  let x = await get('/ask-ai?resource=' + r + '&question=' + encodeURIComponent(q));
  $('answer').textContent = x.answer;
};

async function loadRecommendation(){
    try {
        let x = await get('/recommendation?resource='+r);
        $('recommendation').textContent = x.recommendation;
    } catch(error) {
        $('recommendation').textContent = 'Recommendation unavailable.';
        console.error(error);
    }
}
load();
loadRecommendation();

