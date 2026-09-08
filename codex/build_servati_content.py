#!/usr/bin/env python3
from __future__ import annotations
import argparse,re,subprocess,shutil,json
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

def write_page(root,rel,title,status,typ,src,section,tags,body,era=None):
    p=root/rel; p.parent.mkdir(parents=True,exist_ok=True)
    rows=["---",f"title: {q(title)}",f"status: {q(status)}",f"type: {q(typ)}"]
    if era: rows.append(f"era: {q(era)}")
    rows += [f"source_file: {q(src)}",f"source_section: {q(section)}","tags:"]
    rows += [f"  - {t}" for t in tags]
    rows += ["---","",f"# {title}","",body.strip(),""]
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
    ms=list(re.finditer(r"^##\s+(.+)$",text,re.M))
    return [(m.group(1).strip(),text[m.end():(ms[i+1].start() if i+1<len(ms) else len(text))].strip()) for i,m in enumerate(ms)]

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
    pages=[]

    chapters=list(re.finditer(r"^## Chapter (\d+) - (.+)$",v11,re.M)); app=re.search(r"^# Appendix I -",v11,re.M)
    for i,m in enumerate(chapters):
        num=int(m.group(1)); title=m.group(2).strip(); end=chapters[i+1].start() if i+1<len(chapters) else (app.start() if app else len(v11))
        body=v11[m.end():end].strip(); part=""
        for pm in re.finditer(r"^# Part ([IVX]+) - (.+)$",v11[:m.start()],re.M): part=f"Part {pm.group(1)} — {pm.group(2).strip()}"
        rel=f"history/{num:02d}-{slug(title)}.md"
        write_page(out,rel,f"Chapter {num}: {title}","V11 CORE","chapter",src,f"Chapter {num} - {title}",["canon/v11","type/chapter","history"],body,part)
        pages.append((f"Chapter {num}: {title}",rel,"chapter","V11 CORE"))

    core=[]
    for name,desc in re.findall(r"^\*\*(.+?)\.\*\*\s*(.+)$",section_between(v11,r"^# Appendix I - Core Terms\s*$",r"^# Appendix II -"),re.M):
        rel=f"core-terms/{slug(name)}.md"; write_page(out,rel,name,"V11 CORE","core term",src,"Appendix I - Core Terms",["canon/v11","type/core-term"],desc); core.append((name,rel)); pages.append((name,rel,"core term","V11 CORE"))
    lineages=[]
    for name,era,desc in re.findall(r"^\*\*(.+?)\*\*\s*\((.+?)\)\.\s*(.+)$",section_between(v11,r"^# Appendix II - Principal Custodial Lineages\s*$",r"^# Appendix III -"),re.M):
        rel=f"lineages/{slug(name)}.md"; write_page(out,rel,name,"V11 CORE","lineage",src,"Appendix II - Principal Custodial Lineages",["canon/v11","type/lineage"],desc,era); lineages.append((name,rel)); pages.append((name,rel,"lineage","V11 CORE"))
    envs=[]
    for name,desc in re.findall(r"^\*\*(.+?)\.\*\*\s*(.+)$",section_between(v11,r"^# Appendix III - Principal Environments\s*$",r"^# Appendix IV -"),re.M):
        rel=f"worlds-and-places/{slug(name)}.md"; write_page(out,rel,name,"V11 CORE","environment",src,"Appendix III - Principal Environments",["canon/v11","type/environment","worlds"],desc); envs.append((name,rel)); pages.append((name,rel,"environment","V11 CORE"))

    terms=sorted([x[0] for x in core+lineages+envs],key=len,reverse=True)
    for title,rel,typ,status in [p for p in pages if p[2]=="chapter"]:
        p=out/rel; txt=p.read_text(encoding="utf-8"); hits=[t for t in terms if re.search(rf"(?<!\w){re.escape(t)}(?!\w)",txt,re.I)]
        if hits: p.write_text(txt.rstrip()+"\n\n## Related entries\n\n"+" · ".join(f"[[{h}]]" for h in hits[:18])+"\n",encoding="utf-8")

    drafts=[("drafts/v12/tranche-02/archive-faiths.md","origin/v12-faiths-choirs-custody-wars-20260907:drafts/v12/tranche-02/archive-faiths.md","Archive Faiths"),
            ("drafts/v12/tranche-03/choirs-custody-wars.md","origin/v12-faiths-choirs-custody-wars-20260907:drafts/v12/tranche-03/choirs-custody-wars.md","Choirs + Custody Wars")]
    for work,cand,label in drafts:
        try:text,dsrc=read_source(repo,work,[cand])
        except FileNotFoundError:continue
        rel=f"v12-draft/{slug(label)}.md"; write_page(out,rel,f"V12 DRAFT — {label}","DRAFT","V12 draft tranche",dsrc,label,["draft/v12","type/tranche"],text); pages.append((f"V12 DRAFT — {label}",rel,"V12 draft tranche","DRAFT"))
        for raw,body in split_h2(text):
            if raw.lower() in {"canon anchor","next controlled block"} or re.match(r"^(I|II|III|IV|V|VI|VII|VIII|IX)\.",raw): continue
            name=clean_heading(raw)
            if not name or len(name)>90: continue
            low=(name+" "+body[:300]).lower(); typ="V12 draft entry"
            if "faith" in low or "doctrine" in low: typ="faith / doctrine"
            if "choir logic:" in low or "political form:" in low: typ="Choir civilization"
            if "campaign" in raw.lower() or "war" in name.lower() or "crisis" in low: typ="event / crisis"
            rel=f"v12-draft/entries/{slug(name)}.md"; write_page(out,rel,name,"DRAFT",typ,dsrc,raw,["draft/v12",f"type/{slug(typ)}"],body); pages.append((name,rel,typ,"DRAFT"))

    def portal(rel,title,desc,items):
        write_page(out,rel,title,"CONTROLLED","navigation","generated","portal",["navigation"],desc+"\n\n"+"\n".join(f"- [[{t}]]" for t in items))
    portal("portals/history.md","History & Eras","Browse the controlled Version 11 chapter sequence.",[p[0] for p in pages if p[2]=="chapter"])
    portal("portals/lineages.md","Post-Human Lineages","Principal custodial and post-human lineages.",[p[0] for p in pages if p[2]=="lineage"])
    portal("portals/worlds.md","Worlds & Environments","Principal environments, worlds and custody settings.",[p[0] for p in pages if p[2]=="environment"])
    portal("portals/core-terms.md","Core Terms","Controlled SERVATI vocabulary.",[p[0] for p in pages if p[2]=="core term"])
    portal("portals/v12-draft.md","Version 12 DRAFT","Browsable development material stored in GitHub. DRAFT does not mean canon.",[p[0] for p in pages if p[3]=="DRAFT"])

    index="""**SERVATI: The Worlds That Held the Dead**

A browsable encyclopedia of the controlled SERVATI setting.

> Version 11 is released canon. Version 12 material is displayed as **DRAFT** unless explicitly promoted.

## Browse

- [[History & Eras]]
- [[Post-Human Lineages]]
- [[Worlds & Environments]]
- [[Core Terms]]
- [[Version 12 DRAFT]]

## How to use the Codex

Use Explorer, Search, Random Page, backlinks, tags and internal links. The website is a presentation layer; the SERVATI GitHub repository remains the authoritative project record.
"""
    write_page(out,"index.md","SERVATI Codex","CONTROLLED","navigation","generated","Main Page",["navigation"],index)
    result={"generated_pages":len(list(out.rglob("*.md"))),"chapters":len(chapters),"core_terms":len(core),"lineages":len(lineages),"environments":len(envs),"draft_entries":len([p for p in pages if p[3]=="DRAFT"]),"note":"Tranche 04 excluded until stored in GitHub."}
    (out/"SERVATI_GENERATION_RESULT.json").write_text(json.dumps(result,indent=2),encoding="utf-8"); print(json.dumps(result,indent=2))
if __name__=="__main__": main()
