#!/usr/bin/env python3
from __future__ import annotations
import argparse,html,re,subprocess,shutil,json
from pathlib import Path

def git_show(repo:Path,spec:str):
    p=subprocess.run(["git","-C",str(repo),"show",spec],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding="utf-8")
    return p.stdout if p.returncode==0 else None

def read_source(repo:Path,rel:str,candidates:list[str]):
    p=repo/rel
    if p.exists(): return p.read_text(encoding="utf-8"),rel
    for c in candidates:
        t=git_show(repo,c)
        if t is not None: return t,c
    raise FileNotFoundError(rel)

def slug(s):
    s=re.sub(r"[’'`]","",s.lower().strip())
    return re.sub(r"[^a-z0-9]+","-",s).strip("-") or "page"

def q(s): return '"' + s.replace("\\","\\\\").replace('"','\\"').replace("\n"," ") + '"'

def source_date(repo:Path,spec:str):
    ref,path=(spec.split(":",1) if ":" in spec else ("HEAD",spec))
    p=subprocess.run(["git","-C",str(repo),"log","-1","--format=%cs",ref,"--",path],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding="utf-8")
    return p.stdout.strip() if p.returncode==0 and p.stdout.strip() else None

def wikilink(title,rel): return f"[[{Path(rel).with_suffix('').as_posix()}|{title}]]"

def resolve_bare_links(root,destinations):
    by_title={}
    for title,rel in destinations:
        keys={title.casefold()}
        if title.casefold().startswith("the "): keys.add(title[4:].casefold())
        for key in keys: by_title.setdefault(key,set()).add(rel)
    for p in root.rglob("*.md"):
        text=p.read_text(encoding="utf-8")
        def replace(match):
            title=match.group(1).strip(); matches=by_title.get(title.casefold(),set())
            return wikilink(title,next(iter(matches))) if len(matches)==1 else title
        p.write_text(re.sub(r"\[\[([^\]|#]+)\]\]",replace,text),encoding="utf-8")

def write_page(root,rel,title,status,typ,src,section,tags,body,era=None,modified=None):
    p=root/rel; p.parent.mkdir(parents=True,exist_ok=True)
    rows=["---",f"title: {q(title)}",f"status: {q(status)}",f"type: {q(typ)}"]
    if era: rows.append(f"era: {q(era)}")
    if modified: rows.append(f"modified: {q(modified)}")
    rows += [f"source_file: {q(src)}",f"source_section: {q(section)}","tags:"]
    rows += [f"  - {t}" for t in tags]
    body=re.sub(r"\A#\s+[^\n]+\n+","",body.strip())
    body=re.sub(r"^#(\s+)",r"##\1",body,flags=re.M)
    rows += ["---","",body,""]
    p.write_text("\n".join(rows),encoding="utf-8")

def section_between(text,start_pat,end_pat=None):
    m=re.search(start_pat,text,re.M)
    if not m:return ""
    a=m.end()
    if end_pat:
        n=re.search(end_pat,text[a:],re.M)
        if n:return text[a:a+n.start()]
    return text[a:]

def split_h2(text):
    headings=list(re.finditer(r"^(#{1,2})\s+(.+)$",text,re.M))
    return [
        (m.group(2).strip(),text[m.end():(headings[i+1].start() if i+1<len(headings) else len(text))].strip())
        for i,m in enumerate(headings) if m.group(1)=="##"
    ]

def clean_heading(x):
    x=re.sub(r"^\d+\.\s*","",x.strip())
    x=re.sub(r"\s+[—-]\s+DRAFT$","",x,flags=re.I)
    x=re.sub(r"\s+[—-]\s+V11 CORE name and basis$","",x,flags=re.I)
    return x.strip()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo",required=True); ap.add_argument("--out",required=True); a=ap.parse_args()
    repo=Path(a.repo); out=Path(a.out); marker=out/".servati_generated_content"
    if out.exists() and any(out.iterdir()):
        if not marker.exists(): raise SystemExit(f"Refusing to replace non-generated content directory: {out}")
        shutil.rmtree(out)
    out.mkdir(parents=True,exist_ok=True); marker.write_text("generated\n",encoding="utf-8")

    v11,src=read_source(repo,"SERVATI_V11_AUTHORITATIVE_MANUSCRIPT.md",["origin/main:SERVATI_V11_AUTHORITATIVE_MANUSCRIPT.md","main:SERVATI_V11_AUTHORITATIVE_MANUSCRIPT.md"])
    v11_date=source_date(repo,src)
    pages=[]

    chapters=list(re.finditer(r"^## Chapter (\d+) - (.+)$",v11,re.M)); parts=list(re.finditer(r"^# Part ([IVX]+) - (.+)$",v11,re.M)); app=re.search(r"^# Appendix I -",v11,re.M)
    for i,m in enumerate(chapters):
        num=int(m.group(1)); title=m.group(2).strip(); boundaries=[chapters[i+1].start() if i+1<len(chapters) else (app.start() if app else len(v11))]
        boundaries += [pm.start() for pm in parts if pm.start()>m.start()]
        end=min(boundaries)
        body=v11[m.end():end].strip(); part=""
        for pm in parts:
            if pm.start()>=m.start(): break
            part=f"Part {pm.group(1)} — {pm.group(2).strip()}"
        rel=f"history/{num:02d}-{slug(title)}.md"
        write_page(out,rel,f"Chapter {num}: {title}","V11 CORE","chapter",src,f"Chapter {num} - {title}",["canon/v11","type/chapter","history"],body,part,v11_date)
        pages.append((f"Chapter {num}: {title}",rel,"chapter","V11 CORE"))

    core=[]
    for name,desc in re.findall(r"^\*\*(.+?)\.\*\*\s*(.+)$",section_between(v11,r"^# Appendix I - Core Terms\s*$",r"^# Appendix II -"),re.M):
        rel=f"core-terms/{slug(name)}.md"; write_page(out,rel,name,"V11 CORE","core term",src,"Appendix I - Core Terms",["canon/v11","type/core-term"],desc,modified=v11_date); core.append((name,rel)); pages.append((name,rel,"core term","V11 CORE"))
    lineages=[]
    for name,era,desc in re.findall(r"^\*\*(.+?)\*\*\s*\((.+?)\)\.\s*(.+)$",section_between(v11,r"^# Appendix II - Principal Custodial Lineages\s*$",r"^# Appendix III -"),re.M):
        rel=f"lineages/{slug(name)}.md"; write_page(out,rel,name,"V11 CORE","lineage",src,"Appendix II - Principal Custodial Lineages",["canon/v11","type/lineage"],desc,era,v11_date); lineages.append((name,rel)); pages.append((name,rel,"lineage","V11 CORE"))
    envs=[]
    for name,desc in re.findall(r"^\*\*(.+?)\.\*\*\s*(.+)$",section_between(v11,r"^# Appendix III - Principal Environments\s*$",r"^# Appendix IV -"),re.M):
        rel=f"worlds-and-places/{slug(name)}.md"; write_page(out,rel,name,"V11 CORE","environment",src,"Appendix III - Principal Environments",["canon/v11","type/environment","worlds"],desc,modified=v11_date); envs.append((name,rel)); pages.append((name,rel,"environment","V11 CORE"))

    term_candidates={}
    for title,rel in core+lineages+envs:
        term_candidates.setdefault(title.casefold(),[]).append((title,rel))
    term_links={items[0][0]:items[0][1] for items in term_candidates.values() if len({rel for title,rel in items})==1}
    terms=sorted(term_links,key=len,reverse=True)
    for title,rel,typ,status in [p for p in pages if p[2]=="chapter"]:
        p=out/rel; txt=p.read_text(encoding="utf-8"); hits=[t for t in terms if re.search(rf"(?<!\w){re.escape(t)}(?!\w)",txt,re.I)]
        if hits: p.write_text(txt.rstrip()+"\n\n## Related entries\n\n"+" | ".join(wikilink(h,term_links[h]) for h in hits[:18])+"\n",encoding="utf-8")

    drafts=[("drafts/v12/tranche-02/archive-faiths.md","origin/v12-faiths-choirs-custody-wars-20260907:drafts/v12/tranche-02/archive-faiths.md","Archive Faiths"),
            ("drafts/v12/tranche-03/choirs-custody-wars.md","origin/v12-faiths-choirs-custody-wars-20260907:drafts/v12/tranche-03/choirs-custody-wars.md","Choirs + Custody Wars")]
    draft_dates=[]
    for work,cand,label in drafts:
        try:text,dsrc=read_source(repo,work,[cand])
        except FileNotFoundError:continue
        draft_date=source_date(repo,dsrc); draft_dates.append(draft_date)
        rel=f"v12-draft/{slug(label)}.md"; write_page(out,rel,f"V12 DRAFT — {label}","DRAFT","V12 draft tranche",dsrc,label,["draft/v12","type/tranche"],text,modified=draft_date); pages.append((f"V12 DRAFT — {label}",rel,"V12 draft tranche","DRAFT"))
        for raw,body in split_h2(text):
            if raw.lower() in {"canon anchor","next controlled block"} or re.match(r"^(I|II|III|IV|V|VI|VII|VIII|IX)\.",raw): continue
            name=clean_heading(raw)
            if not name or len(name)>90: continue
            low=(name+" "+body[:300]).lower(); typ="V12 draft entry"
            if "faith" in low or "doctrine" in low: typ="faith / doctrine"
            if "choir logic:" in low or "political form:" in low: typ="Choir civilization"
            if "campaign" in raw.lower() or "war" in name.lower() or "crisis" in low: typ="event / crisis"
            rel=f"v12-draft/entries/{slug(name)}.md"; write_page(out,rel,name,"DRAFT",typ,dsrc,raw,["draft/v12",f"type/{slug(typ)}"],body,modified=draft_date); pages.append((name,rel,typ,"DRAFT"))

    latest_date=max([d for d in [v11_date,*draft_dates] if d],default=None)
    def portal(rel,title,desc,items,modified):
        write_page(out,rel,title,"CONTROLLED","navigation","generated","portal",["navigation"],desc+"\n\n"+"\n".join(f"- {wikilink(t,r)}" for t,r in items),modified=modified)
    portal("portals/history.md","History & Eras","Browse the controlled Version 11 chapter sequence.",[(p[0],p[1]) for p in pages if p[2]=="chapter"],v11_date)
    portal("portals/lineages.md","Post-Human Lineages","Principal custodial and post-human lineages.",[(p[0],p[1]) for p in pages if p[2]=="lineage"],v11_date)
    portal("portals/worlds.md","Worlds & Environments","Principal environments, worlds and custody settings.",[(p[0],p[1]) for p in pages if p[2]=="environment"],v11_date)
    portal("portals/core-terms.md","Core Terms","Controlled SERVATI vocabulary.",[(p[0],p[1]) for p in pages if p[2]=="core term"],v11_date)
    portal("portals/v12-draft.md","Version 12 DRAFT","Browsable development material stored in GitHub. DRAFT does not mean canon.",[(p[0],p[1]) for p in pages if p[3]=="DRAFT"],max([d for d in draft_dates if d],default=None))

    folder_indexes=[
        ("history/index.md","History Register","V11 CORE","Controlled Version 11 chapters. [[portals/history|Open the curated History & Eras portal.]]",v11_date),
        ("core-terms/index.md","Core Terms Register","V11 CORE","Controlled SERVATI vocabulary. [[portals/core-terms|Open the curated Core Terms portal.]]",v11_date),
        ("lineages/index.md","Lineage Register","V11 CORE","Principal custodial and post-human lineages. [[portals/lineages|Open the curated Post-Human Lineages portal.]]",v11_date),
        ("worlds-and-places/index.md","Worlds & Environments Register","V11 CORE","Principal environments, worlds, and custody settings. [[portals/worlds|Open the curated Worlds & Environments portal.]]",v11_date),
        ("v12-draft/index.md","Version 12 Draft Register","DRAFT","Unreleased development material. [[portals/v12-draft|Open the curated Version 12 DRAFT portal.]]",max([d for d in draft_dates if d],default=None)),
        ("v12-draft/entries/index.md","Version 12 Draft Entries","DRAFT","Individual development records extracted from GitHub-hosted draft tranches. [[portals/v12-draft|Open the complete draft portal.]]",max([d for d in draft_dates if d],default=None)),
        ("portals/index.md","Curated Portals","CONTROLLED","Curated routes through the archive registers.",latest_date),
    ]
    for rel,title,status,body,modified in folder_indexes:
        write_page(out,rel,title,status,"archive index","generated","folder index",["navigation"],body,modified=modified)

    portal_specs=[
        ("01","V11 CORE","History & Eras","portals/history",len([p for p in pages if p[2]=="chapter"]),"Controlled chapter sequence and historical eras."),
        ("02","V11 CORE","Post-Human Lineages","portals/lineages",len(lineages),"Principal custodial and post-human lineages."),
        ("03","V11 CORE","Worlds & Environments","portals/worlds",len(envs),"Worlds, environments, and custody settings."),
        ("04","V11 CORE","Core Terms","portals/core-terms",len(core),"Controlled vocabulary and setting definitions."),
        ("05","DRAFT","Version 12 Development","portals/v12-draft",len([p for p in pages if p[3]=="DRAFT"]),"Unreleased development records, visibly separated from canon."),
    ]
    portal_html="\n".join(f'''<a class="archive-portal" href="./{path}">
  <span class="archive-portal-code">REGISTER {code} / {status}</span>
  <strong>{html.escape(title)}</strong>
  <span>{html.escape(desc)}</span>
  <b>{count} records</b>
</a>''' for code,status,title,path,count,desc in portal_specs)
    featured=[]
    for typ in ("chapter","lineage","environment"):
        featured.extend([p for p in pages if p[2]==typ][:2])
    featured_html="\n".join(f'''<a href="./{Path(rel).with_suffix('').as_posix()}">
  <span>{html.escape(typ.upper())}</span>
  <strong>{html.escape(title)}</strong>
  <b class="archive-status archive-status--verified">VERIFIED</b>
</a>''' for title,rel,typ,status in featured)
    index=f"""<p class="archive-kicker">CONTROLLED SETTING ENCYCLOPEDIA / GITHUB-BACKED EDITION</p>
<p class="archive-lede">The Worlds That Held the Dead. A browsable reference for the controlled SERVATI setting.</p>
<div class="archive-status-line" aria-label="Record status legend">
  <span class="archive-status archive-status--verified">V11 CORE / VERIFIED</span>
  <span class="archive-status archive-status--draft">V12 / DRAFT RECORDS</span>
</div>

> Version 11 is released canon. Version 12 material remains **DRAFT** unless explicitly promoted.

## Primary registers

<nav class="archive-portals" aria-label="Primary archive registers">
{portal_html}
</nav>

## Featured records

<div class="archive-featured">
{featured_html}
</div>

## Library actions

<nav class="archive-actions" aria-label="Library actions">
  <a href="./portals/core-terms">Browse controlled vocabulary</a>
  <a href="./portals/v12-draft">Open the draft register</a>
  <a href="https://github.com/Nexlu1/servati">Inspect the source repository</a>
  <a href="https://github.com/Nexlu1/servati/blob/main/SERVATI_V11_AUTHORITATIVE_MANUSCRIPT.md">Read the V11 manuscript</a>
</nav>

Use Search, Archive Registers, Random Record, backlinks, and tags to move through the collection. The GitHub repository remains the authoritative project record.
"""
    write_page(out,"index.md","SERVATI Codex","CONTROLLED","navigation","generated","Main Page",["navigation"],index,modified=latest_date)
    destinations=[(p[0],p[1]) for p in pages]+[(title,f"{path}.md") for code,status,title,path,count,desc in portal_specs]+[(title,rel) for rel,title,status,body,modified in folder_indexes]
    resolve_bare_links(out,destinations)
    result={"generated_pages":len(list(out.rglob("*.md"))),"chapters":len(chapters),"core_terms":len(core),"lineages":len(lineages),"environments":len(envs),"draft_entries":len([p for p in pages if p[3]=="DRAFT"]),"note":"Tranche 04 excluded until stored in GitHub."}
    (out/"SERVATI_GENERATION_RESULT.json").write_text(json.dumps(result,indent=2),encoding="utf-8"); print(json.dumps(result,indent=2))
if __name__=="__main__": main()
