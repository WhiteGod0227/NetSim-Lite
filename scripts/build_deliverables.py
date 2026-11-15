"""Regenerate editable report, PDF, slides and submission source archive."""
from pathlib import Path
from PIL import Image as PILImage
import json
import zipfile
from xml.sax.saxutils import escape
from docx import Document
from docx.shared import Inches as DInches, Pt as DPt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'deliverables'
OUT.mkdir(exist_ok=True)
META={'student':'[Student / team names]','roll':'[Roll numbers]','college':'[College / institution]','guide':'[Guide name]','department':'[Department]','semester':'Semester 5 - confirm with institution','date':'15 November 2026'}
config=OUT/'submission-details.json'
if config.exists(): META.update(json.loads(config.read_text(encoding='utf-8-sig')))
else: config.write_text(json.dumps(META,indent=2),encoding='utf-8')

refs=[
 ('Project brief','NetSim_Lite_Complete_Project_Guide.pdf, supplied by the user; project requirements and demonstration scenarios.'),
 ('FastAPI documentation','https://fastapi.tiangolo.com/'),
 ('React Flow documentation','https://reactflow.dev/'),
 ('Python ipaddress reference','https://docs.python.org/3/library/ipaddress.html'),
 ('Python heapq reference','https://docs.python.org/3/library/heapq.html'),
]

sections=[
('1. Abstract and problem statement',[
 ('p','NetSim Lite is a browser-based educational tool for building network topologies and exploring minimum-cost routing. A user creates computer, router, and switch nodes, connects them with weighted bidirectional links, and chooses source and destination devices. The backend calculates a route, while the frontend highlights the path and animates a logical packet across its hops. Disabling links provides an immediate way to demonstrate route changes and unreachable destinations.'),
 ('p','Networking concepts are often introduced through static diagrams. Those diagrams do not readily show how the chosen path changes when a cost or connection changes. This project makes the graph, route calculation, and delivery outcome visible in a single interface. Its companion IPv4 calculator connects addressing theory with concrete network, mask, broadcast, and usable-host results.'),
 ('p','The implementation combines React, TypeScript, Vite, and React Flow with a FastAPI service. Python heapq supports a custom Dijkstra implementation, and Python ipaddress supports IPv4 calculations. Topologies are saved in browser localStorage. This is a logical graph simulator: the application does not transmit real network traffic or implement Ethernet, routing protocols, or TCP congestion control.'),
 ('p','Keywords: Dijkstra, weighted graph, IPv4, CIDR, link failure, packet visualization, client-server architecture.')]),
('2. Objectives, requirements, and scope',[
 ('bullets',['Create, move, edit, and delete PCs, routers, and switches.','Create bidirectional links with finite non-negative costs; edit, disable, restore, or delete them.','Find minimum-cost routes and report unreachable destinations.','Animate logical packet hops and show events in a log.','Calculate IPv4 network address, prefix, subnet mask, broadcast, host range, and usable-host count.','Save and restore one topology in browser localStorage.']),
 ('p','The primary user is a student or instructor demonstrating introductory computer-network concepts. The default four-node topology is sufficient to show route selection, rerouting, and disconnection without requiring real routers or network privileges.'),
 ('table',[['Requirement','Implemented behavior'],['Usability','Device palette, draggable canvas, properties inspector, route controls, event log'],['Validation','Duplicate device IDs, invalid IPv4 addresses, missing endpoints, invalid costs, duplicate/self-links rejected'],['Reliability','Stale route/subnet responses handled; invalid saved structures rejected'],['Persistence','One browser-local topology; no server database'],['Runtime','Local frontend on 127.0.0.1:5173, backend on 127.0.0.1:8000']]),
 ('p','Excluded features include real packet capture, MAC learning, full OSPF/BGP, actual TCP/UDP transmission, authentication, multi-user editing, and cloud database persistence. Device types are visual categories; their IP metadata does not determine routing adjacency.')]),
('3. Architecture and technology choices',[
 ('p','The browser owns editor state, device positions, selection, animation, and saved topology data. React Flow provides the node-and-edge canvas. React components implement device rendering, packet edges, validated link-cost drafts, and the subnet form. Plain CSS supplies the visual design; Tailwind is not used.'),
 ('code','Browser: React + TypeScript + React Flow\n    | POST /api/route, /api/simulate, /api/subnet\n    v\nVite /api development proxy -> FastAPI + Pydantic\n    |                         |\n    v                         v\nCustom Dijkstra (heapq)    IPv4Network (ipaddress)\n    |                         |\n    +---- JSON response ------+\n    v\nPath highlighting, hop animation, event log\n\nBrowser state <-> localStorage (Save / Load)'),
 ('p','FastAPI validates structured requests through Pydantic models and exposes interactive API documentation. Route requests pass through graph validation before the algorithm executes. The subnet endpoint normalizes host addresses to their network using IPv4Network with strict=False. Errors become HTTP 422 responses with readable messages.'),
 ('p','The guide proposed NetworkX; the delivered application instead uses a small custom heap-based Dijkstra function, making the central algorithm easy to explain in a viva. No database is necessary for the single-browser prototype. The UI uses a 10-second timeout for POST requests and a bounded health check to improve failure feedback.')]),
('4. Data model and API contract',[
 ('table',[['Object','Fields and constraints'],['Device','id: nonblank unique string; label; optional IPv4 ip; kind: pc/router/switch'],['Link','source and target must exist and differ; finite numeric cost >= 0; strict enabled boolean'],['Graph','Undirected, one link per unordered device pair; disabled links excluded from routing'],['Route result','source, destination, path, total_cost, reachable'],['Subnet result','network, prefix, mask, broadcast, first_host, last_host, usable_hosts']]),
 ('table',[['Method / endpoint','Purpose'],['GET /api/health','Returns status: ok'],['POST /api/route','Minimum-cost path and reachability'],['POST /api/simulate','Route plus created/forwarded/delivered or unreachable events'],['POST /api/subnet','IPv4 subnet breakdown from cidr input']]),
 ('code','POST /api/route\n{"nodes":[{"id":"A"},{"id":"B"}],\n "links":[{"source":"A","target":"B",\n           "cost":1,"enabled":true}],\n "source":"A","destination":"B"}\n\nResponse:\n{"source":"A","destination":"B",\n "path":["A","B"],"total_cost":1,"reachable":true}'),
 ('p','An unreachable route returns path: [], total_cost: null, reachable: false. The same-device case returns a one-node path and cost 0. Invalid requests return HTTP 422. Saved topology JSON is validated and reconstructed before replacing current canvas state; arbitrary render types and malformed edge data are not restored.')]),
('5. Routing algorithm and worked example',[
 ('p','Each device is a graph vertex, and each active link is an undirected edge. Dijkstra starts with distance 0 at the source, infinity elsewhere, and a min-heap containing the source. It repeatedly removes the smallest tentative distance, skips obsolete heap entries, and relaxes neighboring edges. When the destination is removed, predecessor references reconstruct the path.'),
 ('code','validate nodes, links, costs and endpoints\nbuild adjacency from enabled links\ndistance[source] = 0; heap = [(0, source)]\nwhile heap is not empty:\n    distance_so_far, u = pop minimum\n    skip if entry is stale\n    if u == destination: reconstruct and return path\n    for each neighbor v with cost w:\n        candidate = distance_so_far + w\n        if candidate improves distance[v]:\n            store distance and predecessor\n            push candidate and v\nreturn unreachable if no representable route exists'),
 ('table',[['Scenario','Chosen route','Cost'],['All links enabled','PC-A -> R1 -> PC-B','1 + 1 = 2'],['PC-A--R1 disabled','PC-A -> R2 -> PC-B','3 + 2 = 5'],['PC-A--R1 and PC-A--R2 disabled','Unreachable','null']]),
 ('p','Non-negative weights are required because a later negative edge could invalidate a distance already selected as minimum. Zero-cost links are valid. Equal-cost alternatives may return either minimum-cost path; the simulator does not model load balancing. For this simple graph and lazy heap implementation, the usual time bound is O((V + E) log V), with O(V + E) storage. Very large floating-point sums receive explicit overflow handling rather than being mislabeled as disconnected.'),
 ('p','Animation advances the packet marker roughly every 800 ms. This is a fixed teaching interval and is unrelated to cost or measured latency. Disabled links remain visible but do not contribute to the adjacency list. Changing route-relevant topology cancels a running animation; moving or selecting a device preserves a calculated route.')]),
('6. IPv4 subnet calculation',[
 ('p','An IPv4 address contains 32 bits. The CIDR prefix specifies how many bits form the network portion; the remaining bits identify host addresses. The calculator accepts an IPv4 network or host/prefix input and normalizes it to the corresponding network. IPv6 is outside this prototype.'),
 ('table',[['Input / result','Value'],['Input','192.168.1.0/26'],['Network bits / host bits','26 / 6'],['Total addresses','2^6 = 64'],['Subnet mask','255.255.255.192'],['Network address','192.168.1.0'],['Broadcast address','192.168.1.63'],['Usable host range','192.168.1.1 - 192.168.1.62'],['Usable host count','62']]),
 ('p','For prefixes below /31, the conventional usable range excludes the network and broadcast addresses. The implementation follows Python ipaddress conventions for /31 point-to-point networks, where both addresses are usable, and /32, where one host address is represented. It does not apply the ordinary subtract-two rule to these exceptions.'),
 ('p','Subnet results are cleared when input changes. A generation counter prevents a slow older response from overwriting newer input. Invalid input displays an error instead of an old successful result. The backend performs authoritative parsing; the frontend does not attempt to implement an independent subnet algorithm.')]),
('7. Verification, results, and bug fixes',[
 ('p','The recorded development checks comprise 14 Python backend/core tests, nine Playwright browser tests, and a successful TypeScript/Vite production build. These demonstrate the tested cases; they do not establish that the application is free of all possible defects. No performance benchmark or large-network capacity claim is made.'),
 ('table',[['Test group','Cases / observed result'],['Routing','Primary path, alternate path, unreachable, reverse direction, zero-cost cycle, same-device routing: pass'],['API validation','Invalid IP, blank ID, negative/string/boolean costs, self/duplicate links, strict enabled state: pass'],['Numeric edge case','Overflow reported explicitly; finite alternatives remain routable: pass'],['Subnetting','/26 expected values, invalid input, /31 and /32 core cases: pass'],['Editor','Creation, editing, deletion, port connections, duplicate prevention: pass'],['State handling','Route preserved on selection/movement; stale endpoints cleared; old results removed on errors: pass'],['Persistence / async','Malformed saved data rejected; slow subnet results ignored after input edits: pass'],['Layout / build','Mobile overflow check and production build: pass']]),
 ('p','The audit fixed route resets caused by selection, stale deleted endpoints, fractional cost input, malformed localStorage restoration, asynchronous subnet races, unhelpful request errors, and missing same-device delivery logs. Backend changes tightened model constraints, supported both local frontend CORS origins, and handled numeric overflow. The launcher now checks ports, waits for backend readiness, and cleans up Windows child interpreters.'),
 ('p','Evidence is stored in verification logs, automated tests, eight actual application screenshots, and a captioned screen recording. The recording uses browser automation; its captions are added for explanation and are not a feature of the simulator UI. The video has no spoken narration.')]),
('8. Installation and demonstration procedure',[
 ('p','Install Python 3.10+ and a Vite-compatible Node.js release (20.19+ or 22.12+). From the project root, create the virtual environment, install requirements, and install frontend packages. Use the lockfile with npm ci for a clean reproduction.'),
 ('code','python -m venv .venv\n.venv\\Scripts\\python -m pip install -r backend/requirements-dev.txt\nnpm.cmd --prefix frontend ci\n.\\start.ps1\n\nApp: http://127.0.0.1:5173\nAPI docs: http://127.0.0.1:8000/docs'),
 ('bullets',['Start with the four-device demo and explain the two alternative costs.','Send a packet and identify route, cost, highlighted links, and delivery events.','Disable the primary link, send again, and explain why the cost rises to 5.','Disable both source links and show the unreachable result.','Restore the preset, edit a device, then show browser Save / Load.','Calculate 192.168.1.0/26 and explain the host count and broadcast.','End by explaining that graph costs and animation intervals are not measured network latency.']),
 ('p','If the page reports connection refused, start the servers; the URL alone does not launch them. If the backend is offline, inspect backend.stderr.log. Keep ports 5173 and 8000 free. A clean browser or different origin will not contain another browser\'s saved topology. Build output alone needs an HTTP server that forwards /api requests to FastAPI.')]),
('9. Limitations, future work, and conclusion',[
 ('p','The simulator routes over an undirected graph. It treats computers, switches, and routers alike for path calculation; no address-based forwarding or subnet reachability rules are applied. Each device has one optional IPv4 metadata field, not per-interface configuration. Duplicate IP detection and multi-interface routing are not implemented.'),
 ('p','Persistence is limited to one browser-local topology. There is no account system, database, collaborative editing, server deployment, or real packet transport. Costs use floating-point arithmetic, so decimal sums can exhibit ordinary floating-point precision effects. Route selection is minimum-cost rather than minimum-hop unless costs happen to make those equivalent.'),
 ('p','Potential extensions include downloadable topology JSON, multiple named saves, latency models, guided exercises, richer device/interface semantics, simulation export, and a separately scoped deployment. These are proposals and are not claimed as delivered features.'),
 ('p','NetSim Lite implements the guide\'s core prototype workflow: topology construction, route calculation, logical packet delivery, link-failure exploration, and IPv4 subnetting. The combination provides a practical teaching aid and an explainable project for demonstrating graph-based networking concepts. Before institutional submission, the student should replace identity placeholders, review the report against the required template, and practice the live demonstration.')]),
('10. References', [('p',f'{i}. {name}: {url}') for i,(name,url) in enumerate(refs,1)]+[('p','Online references checked on 15 November 2026. Implementation claims refer to the source files and tests included in this project, rather than to generic framework capabilities.')])
]

doc=Document(); sec=doc.sections[0]
sec.top_margin=sec.bottom_margin=DInches(.7)
sec.left_margin=sec.right_margin=DInches(.75)
doc.styles['Normal'].font.name='Calibri';doc.styles['Normal'].font.size=DPt(11)
sec.header.paragraphs[0].text='NETSIM LITE  |  COMPUTER NETWORKS PROJECT'
sec.footer.paragraphs[0].text='Educational graph simulation | Review placeholders before submission'
styles=getSampleStyleSheet();styles['Normal'].fontSize=10;styles['Normal'].leading=15
styles['Title'].textColor=colors.HexColor('#135a54')
story=[]
def para(text,style='Normal'):
 story.append(Paragraph(escape(text).replace('\n','<br/>'),styles[style]));story.append(Spacer(1,8))
doc.add_heading('NETSIM LITE',0);doc.add_paragraph('Interactive Network Topology and Packet Routing Simulator',style='Subtitle')
para('NETSIM LITE','Title');para('Interactive Network Topology and Packet Routing Simulator','Heading2');story.append(Spacer(1,35))
for text in ['Computer Networks | Project-Based Learning',META['college'],META['department'],META['semester'],f"Submitted by: {META['student']}",f"Roll numbers: {META['roll']}",f"Guide: {META['guide']}",f"Prepared: {META['date']}"]:
 doc.add_paragraph(text);para(text)
note='Editable submission draft. Institution-specific certificates, signatures, approvals, and declarations are not supplied. Replace bracketed fields and confirm the prescribed format before submitting.'
doc.add_paragraph(note);para(note)
doc.add_page_break();story.append(PageBreak())
doc.add_heading('Contents',1);para('Contents','Heading1')
for title,_ in sections:
 doc.add_paragraph(title);para(title)
doc.add_paragraph('Appendix A. Application screenshots');para('Appendix A. Application screenshots')
for title,blocks in sections:
 doc.add_page_break();doc.add_heading(title,1);story.append(PageBreak());para(title,'Heading1')
 for kind,value in blocks:
  if kind=='p':doc.add_paragraph(value);para(value)
  elif kind=='bullets':
   for item in value:doc.add_paragraph(item,style='List Bullet');para('- '+item)
  elif kind=='code':
   p=doc.add_paragraph();r=p.add_run(value);r.font.name='Consolas';r.font.size=DPt(9)
   para(value,'Code')
  elif kind=='table':
   table=doc.add_table(rows=0,cols=len(value[0]));table.style='Light Shading Accent 1'
   for row in value:
    cells=table.add_row().cells
    for cell,text in zip(cells,row):cell.text=text
   doc.add_paragraph('')
   cols=[145,355] if len(value[0])==2 else [160,230,110]
   t=Table([[Paragraph(escape(text),styles['Normal']) for text in row] for row in value],colWidths=cols,repeatRows=1,hAlign='LEFT')
   t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e1f1ed')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#ccd9dc')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
   story.extend([t,Spacer(1,12)])

shots=[('01-topology.png','Initial four-device topology.'),('02-packet-animation.png','Packet marker during logical hop animation.'),('03-shortest-path.png','Primary route through R1; total cost 2.'),('04-rerouting.png','Primary link disabled; route through R2; cost 5.'),('05-unreachable.png','Both source links disabled; destination unreachable.'),('06-device-properties.png','Added switch with editable name and IPv4 metadata.'),('07-subnet-calculator.png','IPv4 /26 network breakdown and usable-host count.'),('08-input-validation.png','Invalid subnet input rejected.')]
for i in range(0,len(shots),2):
 doc.add_page_break();doc.add_heading(f'Appendix A. Screenshots ({i//2+1}/4)',1);story.append(PageBreak());para(f'Appendix A. Screenshots ({i//2+1}/4)','Heading1')
 for j,(file,caption) in enumerate(shots[i:i+2],i+1):
  image=OUT/'screenshots'/file
  if not image.exists():raise FileNotFoundError(image)
  doc.add_picture(str(image),width=DInches(5.0));doc.add_paragraph(f'Figure {j}. {caption}',style='Caption')
  iw,ih=PILImage.open(image).size
  story.append(Image(str(image),width=330,height=330*ih/iw));para(f'Figure {j}. {caption}')
doc.save(OUT/'NetSim_Lite_Report.docx')
def page_footer(canvas,document):
 canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#64748b'));canvas.drawString(48,28,'NetSim Lite | Educational network simulation');canvas.drawRightString(547,28,str(document.page))
SimpleDocTemplate(str(OUT/'NetSim_Lite_Report.pdf'),pagesize=(595.28,841.89),leftMargin=48,rightMargin=48,topMargin=45,bottomMargin=45,title='NetSim Lite Project Report',author=META['student']).build(story,onFirstPage=page_footer,onLaterPages=page_footer)

prs=Presentation();prs.slide_width=Inches(13.333);prs.slide_height=Inches(7.5)
BG='0A111C';FG='DBE8F4';MUTED='96ACC3';ACCENT='35D5B2'
def box(slide,x,y,w,h,text,size=20,color=FG,bold=False,fill=None):
 shape=slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if fill else MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h))
 if fill:shape.fill.solid();shape.fill.fore_color.rgb=RGBColor.from_string(fill)
 else:shape.fill.background()
 shape.line.fill.background();tf=shape.text_frame;tf.word_wrap=True
 for i,line in enumerate(text.split('\n')):
  p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=line;p.font.size=Pt(size);p.font.name='Aptos';p.font.color.rgb=RGBColor.from_string(color);p.font.bold=bold;p.space_after=Pt(14)
 return shape
def slide(title,subtitle=''):
 s=prs.slides.add_slide(prs.slide_layouts[6]);s.background.fill.solid();s.background.fill.fore_color.rgb=RGBColor.from_string(BG)
 box(s,.5,.23,12,.3,'NETSIM LITE / COMPUTER NETWORKS LAB',10,ACCENT)
 box(s,.5,.78,12,0.8,title,30,bold=True)
 if subtitle:box(s,.5,1.58,12,.55,subtitle,14,MUTED)
 box(s,.5,7.12,11,.25,'Educational graph simulation | '+META['college'],9,MUTED)
 box(s,12.1,7.08,.7,.3,f'{len(prs.slides):02}',11,ACCENT)
 return s
def notes(s,text):s.notes_slide.notes_text_frame.text=text
def bullets(s,items,x=.6,y=2.2,w=11.8,size=23):box(s,x,y,w,4.5,'\n'.join('• '+i for i in items),size)
def screenshot_slide(title,filename,points,note):
 s=slide(title);box(s,.6,2,3,4.7,'\n'.join('• '+v for v in points),19)
 image=OUT/'screenshots'/filename
 iw,ih=PILImage.open(image).size
 width=min(8.85,4.95*iw/ih)
 s.shapes.add_picture(str(image),Inches(3.9+(8.85-width)/2),Inches(1.9),width=Inches(width))
 notes(s,note);return s
s=slide('Build. Route. Observe.','Interactive Network Topology and Packet Routing Simulator')
box(s,.65,2.5,11,1.1,'NETSIM LITE',48,ACCENT,True)
box(s,.65,4,11,2,f"{META['student']}\n{META['roll']} | {META['department']}\nGuide: {META['guide']} | {META['date']}",19)
notes(s,'Replace the title-slide identity placeholders before submission. Introduce the project as a logical graph simulator for teaching routing and subnetting.')
s=slide('The problem and our objective')
bullets(s,['Static diagrams make route changes difficult to observe.','Create an editable graph of network devices and weighted links.','Show the minimum-cost route and logical packet hops.','Explore failed links, unreachable nodes, and IPv4 subnets.'])
notes(s,'Describe the student learning workflow. Avoid claiming actual Ethernet forwarding or real packet transmission.')
s=slide('System architecture','One browser interface, a small Python API, and browser-local persistence')
for x,text in [(.6,'React + TypeScript\nReact Flow canvas'),(4.65,'FastAPI + Pydantic\nValidated JSON API'),(8.7,'Python core\nheapq + ipaddress')]:box(s,x,2.6,3.8,1.7,text,22,FG,fill='16283A')
box(s,3.95,3.1,.7,.6,'→',28,ACCENT);box(s,8,3.1,.7,.6,'→',28,ACCENT)
box(s,.7,5,11.8,1.3,'Vite proxies /api to port 8000.\nSave / Load stores topology in localStorage; no database.',21,MUTED)
notes(s,'The shipped implementation uses custom Dijkstra with heapq, rather than NetworkX. CSS is plain CSS. Device state is sent to the backend; positions stay in the browser.')
s=slide('Dijkstra: choose the lowest total cost')
bullets(s,['All active link costs must be non-negative.','A min-heap selects the smallest tentative distance.','Relax neighboring distances and keep predecessor references.','Reconstruct the route when the destination is selected.','Zero-cost links are valid; cost is not measured latency.'],size=22)
notes(s,'State the usual O((V+E) log V) bound for the simple graph heap implementation. Explain why negative weights invalidate the selection property. The lazy heap skips stale entries.')
s=slide('Worked topology: two paths, one destination')
for x,y,text in [(.9,3.3,'PC-A'),(5.3,2.1,'R1'),(5.3,4.6,'R2'),(10,3.3,'PC-B')]:box(s,x,y,2.1,.8,text,25,FG,True,'18394A')
for x,y,text in [(3.1,2.7,'cost 1'),(7.7,2.7,'cost 1'),(3.1,4.3,'cost 3'),(7.7,4.3,'cost 2')]:box(s,x,y,2,.6,text,21,ACCENT)
box(s,.8,6,12,.6,'Via R1 = 2    |    Via R2 = 5    |    Chosen route: PC-A → R1 → PC-B',21,ACCENT)
notes(s,'Use the actual canvas in the next slide to show physical placement of the links. These labels summarize the four undirected edges.')
screenshot_slide('Shortest path and packet delivery','03-shortest-path.png',['Route through R1','Total cost: 2','Hop events and delivery','800 ms visual hop interval'],'Send a packet in the live app. Cost is an abstract graph weight; the fixed animation interval does not simulate latency.')
screenshot_slide('Link failure and rerouting','04-rerouting.png',['Disable PC-A–R1','Recalculate the route','Alternative via R2','New total cost: 5'],'Disabled links are excluded when building the adjacency list. Rerouting happens on the next route/simulation request, not automatically at failure time.')
screenshot_slide('Disconnected destination','05-unreachable.png',['Disable both source links','No available path','reachable = false','No delivery completion'],'Show the unreachable message and explain that a disconnected graph is different from malformed input, which receives an HTTP validation error.')
screenshot_slide('IPv4 subnet calculation','07-subnet-calculator.png',['Input: /26','64 total addresses','62 usable hosts','Broadcast: .63'],'Explain 32 minus 26 equals 6 host bits. Normal prefixes exclude network and broadcast; /31 and /32 follow ipaddress exceptions.')
screenshot_slide('Topology editing and persistence','06-device-properties.png',['Add and move devices','Edit label and IP','Set costs / link state','Save / Load in browser'],'Device IPs are metadata, not routing rules. Browser storage is specific to the browser/origin and stores one topology.')
s=slide('Verification and reliability','Observed development results; no claim of exhaustive correctness')
for x,num,label in [(.7,'14','Backend / core tests'),(4.8,'9','Browser tests'),(8.9,'PASS','Production build')]:box(s,x,2.4,3.65,1.9,num,48,ACCENT,True,'15273A');box(s,x,4.35,3.7,.6,label,19)
box(s,.8,5.4,11.8,1.2,'Validation • failure rerouting • zero-cost links • state races\nMalformed saves • fractional costs • reverse routes • mobile overflow',20,MUTED)
notes(s,'Refer to verification logs and BUGFIXES.md. Automated tests establish behavior for those scenarios, not a universal zero-bug guarantee.')
s=slide('Scope and limitations')
bullets(s,['Undirected weighted graphs; devices share graph behavior.','No actual TCP/IP, Ethernet switching, OSPF/BGP, or packet capture.','IP addresses do not govern connectivity; one IP field per device.','One browser-local save; no accounts or server database.','Future work: JSON export, named saves, interface-aware models.'],size=22)
notes(s,'Present future work as proposed, not delivered. Mention floating-point precision limits if asked.')
s=slide('Live demonstration and conclusion')
bullets(s,['Send PC-A → PC-B: cost 2.','Disable the upper link: reroute with cost 5.','Disable both source links: destination unreachable.','Calculate 192.168.1.0/26; explain 62 usable hosts.','NetSim Lite makes graph routing and subnetting observable.'],size=23)
notes(s,'Use demo-script.md to rehearse. A captioned browser screen recording is supplied as a fallback; it has no narration.')
s=slide('References and questions')
box(s,.7,2,12,4.8,'\n'.join(f'{name}\n{url}' for name,url in refs),15,MUTED)
notes(s,'References were checked on 15 November 2026. The source and test suite are the evidence for the implementation. Invite questions about Dijkstra, costs, subnetting, and the client-server flow.')
prs.save(OUT/'NetSim_Lite_Presentation.pptx')

print(f'Generated report DOCX/PDF and {len(prs.slides)} slides.')
