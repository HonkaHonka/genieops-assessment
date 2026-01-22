import asyncio
import re
import os
import httpx
import random
import datetime
import smtplib
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.db.session import get_db, SessionLocal
from app.services.llm_service import engine 
from app.models.lead_magnet import LeadMagnet, Lead 
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

# --- UTILITIES ---

def is_light_color(hex_color):
    try:
        c = hex_color.lstrip('#')
        rgb = tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
        return (0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2])/255 > 0.6
    except: return False

async def get_pro_image(keyword: str, icp: str):
    """Fetches high-quality photo with manual industry context injection"""
    api_key = os.getenv("PEXELS_API_KEY")
    clean_kw = re.sub(r'[^\w\s]', '', str(keyword))
    icp_low = icp.lower()
    
    # HARDENING: Force industry context to stop generic results
    niche = "modern"
    if "bakery" in icp_low or "bread" in icp_low: niche = "bakery food"
    elif "trading" in icp_low or "stock" in icp_low: niche = "finance market"
    elif "yoga" in icp_low or "wellness" in icp_low: niche = "yoga studio"
    elif "security" in icp_low or "cyber" in icp_low: niche = "cyber security office"

    url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(f'{niche} {clean_kw}')}&per_page=1&page={random.randint(1,20)}"
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers={"Authorization": api_key}, timeout=10.0)
            data = resp.json()
            if data.get('photos'): return data['photos'][0]['src']['large2x']
            return "https://images.pexels.com/photos/3184291/pexels-photo-3184291.jpeg"
        except: return "https://images.pexels.com/photos/3184291/pexels-photo-3184291.jpeg"

def send_real_email(to_email, subject, body):
    sender, pw = os.getenv("GMAIL_USER"), os.getenv("GMAIL_PASSWORD")
    if not sender or not pw: return False
    msg = MIMEMultipart()
    msg['From'] = f"GenieOps Engine <{sender}>"; msg['To'] = to_email; msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        print(f"--- [SMTP] Connecting to Gmail for {to_email}... ---")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, pw); server.send_message(msg)
        print(f"+++ [SMTP SUCCESS] Delivered to {to_email} +++")
        return True
    except Exception as e:
        print(f"!!! [SMTP ERROR] {str(e)} !!!")
        return False

async def run_real_nurture(lead_id: int, magnet_id: int):
    await asyncio.sleep(60) 
    db = SessionLocal()
    try:
        magnet = db.query(LeadMagnet).filter(LeadMagnet.id == magnet_id).first()
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead and magnet and magnet.email_nurture_sequence:
            email_data = magnet.email_nurture_sequence[1]
            send_real_email(lead.email, email_data['subject'], email_data['body'])
            lead.nurture_stage = 2; db.commit()
    finally: db.close()

# --- SCHEMAS ---
class GenerationRequest(BaseModel):
    icp_profile: str; pain_points: str; brand_voice: str; offer_type: str; conversion_goal: str
class LeadCapture(BaseModel):
    email: str; magnet_id: int; news_opt_in: bool = False

# --- ENDPOINTS ---

@router.post("/chat-to-funnel")
async def chat_to_funnel(prompt: str, db: Session = Depends(get_db)):
    brief = await engine.interpret_user_prompt(prompt)
    if "error" in brief: raise HTTPException(status_code=500, detail="AI failed to interpret brief")
    return {"status": "brief_ready", "brief": brief}

@router.post("/generate-idea")
async def generate_idea(request: GenerationRequest, db: Session = Depends(get_db)):
    data = await engine.get_strategy_and_theme(request.icp_profile, request.pain_points, request.offer_type, request.conversion_goal)
    if "error" in data: raise HTTPException(status_code=500, detail=data["error"])
    title = re.sub(r'\[|\]|\{|\}', '', str(data.get("title", "Modern Growth")))
    new_entry = LeadMagnet(
        icp_profile=request.icp_profile, pain_points=request.pain_points,
        brand_voice=request.brand_voice, offer_type=request.offer_type,
        conversion_goal=request.conversion_goal, idea_title=title,
        idea_type=str(data.get("type", "Checklist")), 
        value_promise=str(data.get("value_promise", "Expert Strategy")),
        conversion_score=int(data.get("conversion_score", 92)),
        asset_data=data 
    )
    db.add(new_entry); db.commit(); db.refresh(new_entry)
    return {"id": new_entry.id, "strategy": data}

@router.post("/generate-full-asset/{item_id}")
async def generate_full_asset(item_id: int, db: Session = Depends(get_db)):
    lead_magnet = db.query(LeadMagnet).filter(LeadMagnet.id == item_id).first()
    if not lead_magnet: raise HTTPException(status_code=404, detail="Not found")

    theme_data = lead_magnet.asset_data or {}
    url = f"http://localhost:8000/api/v1/preview/{item_id}"
    
    # DeepSeek R1 generates all content and logic
    ds_res = await engine.build_funnel_and_asset(lead_magnet.idea_title, lead_magnet.icp_profile, lead_magnet.idea_type, lead_magnet.brand_voice, lead_magnet.conversion_goal, url)
    if "error" in ds_res: raise HTTPException(status_code=500, detail=ds_res["error"])

    # 1. Fetch Hardened Images
    bg_img = await get_pro_image(theme_data.get('bg_keyword', 'interior'), lead_magnet.icp_profile)
    detail_img = await get_pro_image(theme_data.get('image_keyword', 'product'), lead_magnet.icp_profile)
    li_img = await get_pro_image(theme_data.get('li_image_keyword', 'success'), lead_magnet.icp_profile)

    hex_c = theme_data.get('primary_hex', '#1e293b')
    is_l = is_light_color(hex_c)
    txt_on_btn = "text-slate-900" if is_l else "text-white"
    txt_main = "text-slate-950" if is_l else "text-white"
    overlay_style = f"background-color: {hex_c}E6; backdrop-blur: 12px;"

    # 2. Render UI Components
    logic = ds_res.get('asset_logic', {})
    features = ds_res.get('features', ["Strategic Insights", "Autonomous Design", "Nurture Engine"])
    teaser = f"Calculating {logic.get('input_label')}..." if lead_magnet.idea_type == "Calculator" else "Reviewing expert tips..."

    # --- LANDING PAGE (Long-Form) ---
    lp_template = f"""
    <section class='font-sans bg-black text-white overflow-x-hidden selection:bg-{hex_c}/30'>
        <div class='relative min-h-screen flex items-center justify-center border-b border-white/5'>
            <div class="absolute inset-0 z-0"><img src="{bg_img}" class="w-full h-full object-cover"><div class="absolute inset-0" style="{overlay_style}"></div></div>
            <div class='relative z-10 max-w-7xl mx-auto px-6 grid lg:grid-cols-2 gap-20 py-20 items-center'>
                <div class='max-w-xl text-left'>
                    <div style='background-color: rgba(255,255,255,0.1); border: 1px solid currentColor;' class='inline-block px-5 py-2 rounded-full text-[10px] font-black mb-8 border uppercase tracking-widest text-white'>{lead_magnet.idea_type}</div>
                    <h1 class='text-6xl font-black mb-8 leading-tight tracking-tighter text-white uppercase'>{ds_res.get('headline', lead_magnet.idea_title)}</h1>
                    <p class='text-2xl opacity-80 mb-12 font-light text-slate-300'>{ds_res.get('sub', lead_magnet.value_promise)}</p>
                    <button onclick="document.getElementById('gate').scrollIntoView({{behavior: 'smooth'}})" style='border-color: {hex_c}' class="px-10 py-5 border-2 rounded-2xl font-black uppercase tracking-tighter hover:bg-white hover:text-black transition">Learn More ↓</button>
                </div>
                <div class='bg-white p-12 rounded-[4rem] shadow-2xl relative'><img src='{detail_img}' class='rounded-[2.5rem] mb-6 w-full h-72 object-cover shadow-2xl'><div class='p-6 bg-slate-50 rounded-3xl text-center italic text-slate-500 font-medium font-serif'>{teaser}</div></div>
            </div>
        </div>
        <div class='bg-white py-32 px-6'><div class='max-w-4xl mx-auto text-center text-slate-900'>
            <h2 class='text-5xl font-black mb-8 tracking-tighter uppercase italic'>The Problem</h2>
            <p class='text-slate-600 text-2xl leading-relaxed font-serif italic'>"{ds_res.get('agitation', 'Hidden industry gaps are costing your business money.')}"</p>
        </div></div>
        <div class='bg-slate-50 py-32 px-6 border-y border-slate-200'><div class='max-w-6xl mx-auto text-center'>
            <h2 class='text-slate-900 text-4xl font-black mb-16 uppercase tracking-widest'>The Solution</h2>
            <div class='grid md:grid-cols-3 gap-12'>
                { "".join([f"<div class='bg-white p-10 rounded-[3rem] shadow-xl border border-slate-100 hover:-translate-y-2 transition duration-500'><div style='background-color: {hex_c}' class='w-12 h-12 rounded-2xl mb-8 flex items-center justify-center text-white font-bold'>{i+1}</div><p class='text-slate-900 font-black text-xl mb-4 uppercase tracking-tighter'>INSIGHT_{i+1}</p><p class='text-slate-500 leading-relaxed text-center'>{f}</p></div>" for i, f in enumerate(features)]) }
            </div>
        </div></div>
        <div id='gate' class='py-40 bg-white px-6'><div class='max-w-xl mx-auto bg-slate-950 p-12 rounded-[4rem] text-center shadow-2xl'>
            <h3 class='text-3xl font-black text-white mb-6 uppercase tracking-tighter italic'>Get Instant Access</h3>
            <form class='space-y-6'>
                <input type='email' required placeholder='Enter work email' class='w-full p-6 bg-white/5 border border-white/10 rounded-3xl text-white outline-none focus:border-white transition-all text-center text-xl'>
                <div class='px-4 space-y-4 text-left'>
                    <label class='flex items-center gap-3 text-slate-500 text-xs'><input type='checkbox' required class='w-5 h-5 rounded'> I agree to Terms & Data Protocol</label>
                    <label class='flex items-center gap-3 text-slate-500 text-xs'><input type='checkbox' id='newsletter' class='w-5 h-5 rounded'> Send daily insights & offers</label>
                </div>
                <button type='submit' style='background-color: {hex_c}' class='w-full py-6 {txt_on_btn} font-black text-2xl rounded-3xl uppercase active:scale-95 transition shadow-2xl'>DEPLOY {lead_magnet.idea_type.upper()}</button>
            </form>
        </div></div>
    </section>"""

    # --- THANK YOU PAGE ASSEMBLY ---
    if lead_magnet.idea_type == "Report":
        data_pts = logic.get('data_points', [{'label': 'Potential', 'value': 85}])
        report_viz = "".join([f"<div class='mb-6'><div class='flex justify-between mb-2 text-slate-700 text-sm font-bold uppercase'><span>{d['label']}</span><span>{d['value']}%</span></div><div class='h-3 bg-slate-100 rounded-full overflow-hidden'><div style='width: {d['value']}%; background-color: {hex_c}' class='h-full shadow-lg'></div></div></div>" for d in data_pts])
        asset_ui = f"<div class='bg-white p-10 rounded-[3rem] border border-slate-100 shadow-sm'><h2 class='text-2xl font-black mb-6 text-slate-800 border-b pb-4 text-center'>Market Analysis</h2>{report_viz}</div>"
    elif lead_magnet.idea_type == "Calculator":
        m = logic.get('multiplier', 1.5); u = logic.get('unit', '$'); lab = logic.get('input_label', 'Data')
        asset_ui = f"<div class='text-center p-10 bg-slate-50 rounded-[3rem] border-2 border-dashed border-slate-200'><p class='text-sm font-black text-slate-400 mb-4 uppercase tracking-widest'>{lab}</p><input type='number' id='liveCalc' value='10' oninput='updateCalc()' class='text-7xl font-black text-center w-full bg-transparent outline-none mb-4' style='color:{hex_c}'><p class='text-xl font-bold text-slate-600 font-sans'>Result: <span id='resVal' style='color:{hex_c}'>{u}0</span></p><script>function updateCalc() {{ const v = document.getElementById('liveCalc').value; document.getElementById('resVal').innerText = '{u}' + (v * {m}).toLocaleString(); }} updateCalc();</script></div>"
    else:
        raw_tips = logic.get('tips', ['Review strategy 1', 'Review strategy 2'])
        clean_tips = [next(iter(t.values())) if isinstance(t, dict) else str(t) for t in raw_tips]
        tips_html = "".join([f"<li class='flex items-center gap-4 font-bold text-lg mb-3 text-slate-700 font-sans text-left'><div style='background-color:{hex_c}' class='h-3 w-3 rounded-full shadow-lg'></div> {t}</li>" for t in clean_tips])
        asset_ui = f"<ul class='space-y-4'>{tips_html}</ul>"

    ty_template = f"""<section class='relative min-h-screen flex items-center justify-center font-sans overflow-hidden p-6'><div class="absolute inset-0 z-0"><img src="{bg_img}" class="w-full h-full object-cover"><div class="absolute inset-0 bg-slate-950/95 backdrop-blur-xl" style="background-color: {hex_c}F2;"></div></div><div class='relative z-10 max-w-4xl w-full'><div class='bg-white p-12 rounded-[4rem] shadow-2xl border-t-[16px]' style='border-color: {hex_c}'><h1 class='text-4xl font-black mb-8 text-slate-950 uppercase text-center tracking-tighter'>Results Ready</h1><div class='mb-12'>{asset_ui}</div><div class='text-center p-12 rounded-[3.5rem] text-white shadow-2xl border border-white/20' style='background-color: {hex_c}'><h3 class='text-3xl font-black mb-4 uppercase tracking-tighter'>Exclusive Offer</h3><p class='text-xl mb-10 opacity-90 font-medium'>{ds_res.get('upgrade_offer_copy', 'Special consulting discount.')}</p><button onclick='window.location.href=\"http://localhost:5173/?view=pricing\"' class='px-12 py-5 bg-white text-slate-900 font-black text-xl rounded-2xl shadow-xl uppercase tracking-widest hover:scale-105 transition'>Unlock Pro version</button></div></div></div></section>"""

    # Cleanup and Save
    li_post = str(ds_res.get("linkedin_post", "New tool released!"))
    if isinstance(li_post, dict): li_post = next(iter(li_post.values()))
    li_post = re.sub(r'\{.*?:', '', str(li_post)).replace('}', '').replace('"', '').strip()

    lead_magnet.landing_page_html, lead_magnet.thank_you_html = lp_template, ty_template
    lead_magnet.linkedin_post, lead_magnet.linkedin_img = li_post, li_img
    lead_magnet.email_nurture_sequence = ds_res.get("emails", [])
    lead_magnet.asset_data = logic; db.commit()
    return {"status": "success"}

@router.post("/capture-lead")
async def capture_lead(request: LeadCapture, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    new_lead = Lead(email=request.email, magnet_id=request.magnet_id, subscribed_to_newsletter=request.news_opt_in)
    db.add(new_lead); db.commit(); db.refresh(new_lead)
    
    magnet = db.query(LeadMagnet).filter(LeadMagnet.id == request.magnet_id).first()
    if magnet and magnet.email_nurture_sequence:
        welcome = magnet.email_nurture_sequence[0]
        send_real_email(request.email, welcome['subject'], welcome['body'])
    if request.news_opt_in:
        background_tasks.add_task(run_real_nurture, new_lead.id, request.magnet_id)
    return {"status": "success", "redirect": f"http://localhost:8000/api/v1/preview-thank-you/{request.magnet_id}"}

@router.get("/preview/{item_id}", response_class=HTMLResponse)
async def preview_landing_page(item_id: int, db: Session = Depends(get_db)):
    lead_magnet = db.query(LeadMagnet).filter(LeadMagnet.id == item_id).first()
    if not lead_magnet or not lead_magnet.landing_page_html: return "<h1>Generating...</h1>"
    return f"<!DOCTYPE html><html><head><script src='https://cdn.tailwindcss.com'></script></head><body class='antialiased'>{lead_magnet.landing_page_html}<script>document.querySelector('form').addEventListener('submit', async (e) => {{ e.preventDefault(); const em = e.target.querySelector('input').value; const news = document.getElementById('newsletter').checked; if(!em.includes('@')) {{alert('Valid email required'); return;}} const res = await fetch('http://localhost:8000/api/v1/capture-lead', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{ email: em, magnet_id: {item_id}, news_opt_in: news }}) }}); const data = await res.json(); if(data.redirect) {{ window.location.href = data.redirect; }} }});</script></body></html>"

@router.get("/preview-thank-you/{item_id}", response_class=HTMLResponse)
async def preview_thank_you(item_id: int, db: Session = Depends(get_db)):
    lead_magnet = db.query(LeadMagnet).filter(LeadMagnet.id == item_id).first()
    return f"<!DOCTYPE html><html><head><script src='https://cdn.tailwindcss.com'></script></head><body>{lead_magnet.thank_you_html}</body></html>"

@router.get("/lead-magnets-all")
def get_all_lead_magnets(db: Session = Depends(get_db)):
    return db.query(LeadMagnet).order_by(LeadMagnet.created_at.desc()).all()