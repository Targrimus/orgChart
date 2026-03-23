import csv
import json
import os
import base64

csv_file = "BAĞIMLILIKLAR.csv"
output_file = "org_chart.html"

employees = {}

with open(csv_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        sicil = row.get('SİCİL')
        if not sicil: continue
        
        emp = {
            'sicil': sicil,
            'ad_soyad': row.get('ADI SOYADI'),
            'unvan': row.get('POZİSYON'),
            'bolum': row.get('BÖLÜM'),
            'calisma_yeri': row.get('ÇALIŞMA YERİ'),
            'bagli_sicil': row.get('BAĞLI SİCİL'),
            'bagli_personeller': []
        }
        employees[sicil] = emp

        # Also add root manually if its not explicitly defined as its own employee row
        bagli_sicil = row.get('BAĞLI SİCİL')
        if bagli_sicil and bagli_sicil not in employees:
            if bagli_sicil == '0':
                employees['0'] = {
                    'sicil': '0',
                    'ad_soyad': row.get('BAĞLI ADI SOYADI'),
                    'unvan': row.get('BAĞLI POZİSYON'),
                    'bolum': row.get('BAĞLI BÖLÜM'),
                    'calisma_yeri': row.get('BAĞLI ÇALIŞMA YERİ'),
                    'bagli_sicil': None,
                    'bagli_personeller': []
                }

# Build hierarchy
root_nodes = []
for sicil, emp in employees.items():
    bagli_sicil = emp.get('bagli_sicil')
    if bagli_sicil in employees and bagli_sicil != sicil:
        employees[bagli_sicil]['bagli_personeller'].append(emp)
    else:
        if sicil != '0':
            root_nodes.append(emp)

if '0' in employees:
    root_nodes = [employees['0']]

root_data = root_nodes[0] if root_nodes else {}

html_template = """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Organizasyon Şeması (Müdür -> Şube -> Şef/Mühendis/Ünvan)</title>
    <!-- CSS and Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    
    <!-- D3.js and OrgChart -->
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/d3-org-chart@3"></script>
    <script src="https://cdn.jsdelivr.net/npm/d3-flextree@2.1.2/build/d3-flextree.js"></script>
    
    <style>
        body {
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f1f5f9;
            overflow: hidden;
        }
        #header {
            background: #ffffff;
            padding: 15px 30px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: relative;
            z-index: 10;
        }
        #header h1 {
            margin: 0;
            font-size: 20px;
            color: #0f172a;
            font-weight: 800;
            letter-spacing: -0.5px;
        }
        .controls {
            display: flex;
            gap: 10px;
        }
        .controls button {
            background-color: #f8fafc;
            color: #334155;
            border: 1px solid #cbd5e1;
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        .controls button:hover {
            background-color: #e2e8f0;
            color: #0f172a;
        }
        .controls button.primary {
            background-color: #2563eb;
            color: white;
            border-color: #1d4ed8;
            box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
        }
        .controls button.primary:hover {
            background-color: #1d4ed8;
        }
        
        .legend {
            display: flex;
            gap: 15px;
            margin-right: 25px;
            align-items: center;
            font-size: 13px;
            font-weight: 600;
            color: #475569;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .color-box {
            width: 14px;
            height: 14px;
            border-radius: 4px;
            box-shadow: inset 0 0 0 1px rgba(0,0,0,0.1);
        }
        
        #chart-container {
            height: calc(100vh - 65px);
            width: 100%;
            background-color: #f1f5f9;
        }

        /* Grouped Node scrollbar styling */
        .group-scroll::-webkit-scrollbar {
            width: 6px;
        }
        .group-scroll::-webkit-scrollbar-track {
            background: #f8fafc; 
            border-radius: 4px;
        }
        .group-scroll::-webkit-scrollbar-thumb {
            background: #cbd5e1; 
            border-radius: 4px;
        }
        .group-scroll::-webkit-scrollbar-thumb:hover {
            background: #94a3b8; 
        }
    </style>
</head>
<body>
    <div id="header">
        <h1>Organizasyon Şeması</h1>
        <div style="display: flex; align-items: center;">
            <div class="legend">
                <div class="legend-item"><div class="color-box" style="background-color: #ef4444;"></div>Genel Müdür</div>
                <div class="legend-item"><div class="color-box" style="background-color: #f97316;"></div>Müdür</div>
                <div class="legend-item"><div class="color-box" style="background-color: #8b5cf6;"></div>Yönetmen</div>
                <div class="legend-item"><div class="color-box" style="background-color: #10b981;"></div>Şef / Mühendis</div>
                <div class="legend-item"><div class="color-box" style="background-color: #64748b;"></div>Görev Tanımı (Yaprak)</div>
            </div>
            <div class="controls">
                <button onclick="chart.expandAll()">↓ Genişlet</button>
                <button onclick="chart.collapseAll()">↑ Daralt</button>
                <button class="primary" onclick="chart.fit()">⛶ Sığdır</button>
            </div>
        </div>
    </div>
    <div id="chart-container"></div>
    
    <script id="b64Data" type="text/plain">
JSON_PLACEHOLDER
    </script>

    <script>
        const b64Data = document.getElementById('b64Data').textContent.replace(/\\s+/g, '');
        const binString = atob(b64Data);
        const bytes = new Uint8Array(binString.length);
        for (let i = 0; i < binString.length; i++) {
            bytes[i] = binString.charCodeAt(i);
        }
        const rawData = JSON.parse(new TextDecoder("utf-8").decode(bytes));
        const rootData = Array.isArray(rawData) ? rawData[0] : rawData;

        const flatData = [];
        const seenIds = new Set();
        
        function getId(prefix) {
            let id = prefix + "_" + Math.random().toString(36).substr(2, 9);
            while (seenIds.has(id)) { id = prefix + "_" + Math.random().toString(36).substr(2, 9); }
            seenIds.add(id);
            return id;
        }

        // Ana İşleme Fonksiyonu
        function buildTree(node, parentId = null) {
            if (!node) return;
            
            // Kendi çalışma yerini hesapla
            let managerLoc = node.calisma_yeri && node.calisma_yeri !== "-" ? node.calisma_yeri : "Belirtilmemiş Lokasyon";
            
            // Bu düğüm MÜDÜR mü (veya tepe yönetici mi)?
            let unvan = (node.unvan || "").toUpperCase();
            let isMudur = unvan.includes("MÜDÜR") || parentId === null;

            if (isMudur) {
                let managerId = getId("mgr");
                flatData.push({
                    id: managerId,
                    parentId: parentId,
                    isManager: true,
                    name: node.ad_soyad || "İsimsiz Yönetici",
                    positionName: node.unvan || "Unvan Belirtilmemiş",
                    department: managerLoc,
                    subeInfo: managerLoc
                });

                let nonMudurDescendants = [];
                let childMudurs = [];
                
                function collectDescendants(curr_node) {
                    if (!curr_node.bagli_personeller) return;
                    
                    curr_node.bagli_personeller.forEach(child => {
                        // Çalışma yeri grup ismini belirle
                        let childLoc = child.calisma_yeri && child.calisma_yeri !== "-" ? child.calisma_yeri : "Belirtilmemiş Lokasyon";
                        let c_unvan = (child.unvan || "").toUpperCase();
                        
                        if (c_unvan.includes("MÜDÜR")) {
                            childMudurs.push({ node: child });
                        } else {
                            child._computedSube = childLoc;
                            nonMudurDescendants.append(child);
                            collectDescendants(child);
                        }
                    });
                }
                
                nonMudurDescendants.append = function(e) { this.push(e); };
                
                collectDescendants(node);

                // Toplanan Şef, Mühendis ve Görevlileri (Lokasyon -> Ünvan) şeklinde grupla
                const groups = {};
                nonMudurDescendants.forEach(emp => {
                    let s_name = emp._computedSube;
                    let u_name = emp.unvan || "Belirtilmemiş Ünvan";
                    
                    if (!groups[s_name]) groups[s_name] = {};
                    if (!groups[s_name][u_name]) groups[s_name][u_name] = [];
                    groups[s_name][u_name].push(emp);
                });

                // Şube (Çalışma Yeri) Düğümlerini oluştur
                Object.keys(groups).forEach(s_name => {
                    let subeId = getId("sube");
                    let totalPeople = Object.values(groups[s_name]).reduce((acc, curr) => acc + curr.length, 0);
                    
                    flatData.push({
                        id: subeId,
                        parentId: managerId,
                        isSubeNode: true,
                        name: s_name,
                        count: totalPeople
                    });

                    // Şubenin Altındaki Şefler, Mühendisler ve Görevlileri (Ünvan) Düğüm olarak ekle
                    Object.keys(groups[s_name]).sort().forEach(u_name => {
                        let unvanId = getId("unvan");
                        let emps = groups[s_name][u_name];
                        let names = emps.map(e => e.ad_soyad || "İsimsiz").sort();
                        
                        flatData.push({
                            id: unvanId,
                            parentId: subeId,
                            isTitleGroup: true,
                            positionName: u_name,
                            names: names,
                            count: names.length
                        });
                    });
                });

                childMudurs.forEach(cm => {
                    buildTree(cm.node, managerId);
                });
            }
        }
        
        buildTree(rootData);

        let chart = new d3.OrgChart()
            .container('#chart-container')
            .data(flatData)
            .nodeWidth(d => {
                if (d.data.isManager) return 280;
                if (d.data.isSubeNode) return 240;
                return 280;
            })
            .nodeHeight(d => {
                if (d.data.isManager) return 120;
                if (d.data.isSubeNode) return 80;
                return 100 + Math.min(d.data.count * 20, 160); 
            })
            .childrenMargin(d => 60)
            .compactMarginBetween(d => 35)
            .compactMarginPair(d => 60)
            .nodeContent(function(d) {
                if (d.data.isManager) {
                    const unvan = (d.data.positionName || "").toUpperCase();
                    let borderColor = "#3b82f6";
                    let bgColor = "#ffffff";
                    
                    if (unvan.includes("GENEL MÜDÜR")) {
                        borderColor = "#ef4444"; bgColor = "#fef2f2";
                    } else if (unvan.includes("MÜDÜR")) {
                        borderColor = "#f97316"; bgColor = "#fff7ed";
                    }

                    return `
                        <div style="background-color: ${bgColor}; border: 1px solid #cbd5e1; border-radius: 12px; width: ${d.width}px; height: ${d.height}px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); display: flex; flex-direction: column; justify-content: center; align-items: center; border-top: 6px solid ${borderColor}; padding: 12px; box-sizing: border-box;">
                            <div style="font-size: 16px; font-weight: 900; color: #0f172a; margin-bottom: 8px; text-align: center; width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${d.data.name}">
                                👤 ${d.data.name}
                            </div>
                            <div style="font-size: 13px; font-weight: 700; color: #475569; text-align: center; background: white; padding: 6px 14px; border-radius: 20px; border: 1px solid #e2e8f0; width: 90%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${d.data.positionName}">
                                ${d.data.positionName}
                            </div>
                        </div>
                    `;
                }

                if (d.data.isSubeNode) {
                    return `
                        <div style="background-color: #eff6ff; border: 2px solid #3b82f6; border-radius: 12px; width: ${d.width}px; height: ${d.height}px; display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                            <div style="font-size: 14px; font-weight: 800; color: #1e40af; text-align: center; width: 90%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 6px;" title="${d.data.name}">
                                📍 ${d.data.name}
                            </div>
                            <div style="font-size: 12px; font-weight: 700; color: #2563eb; background: #dbeafe; padding: 4px 10px; border-radius: 20px;">
                                Yaka / Ekip: ${d.data.count}
                            </div>
                        </div>
                    `;
                }

                if (d.data.isTitleGroup) {
                    const unvan = (d.data.positionName || "").toUpperCase();
                    let borderColor = "#cbd5e1"; // Gri (Diğer)
                    let icon = "🧑‍🔧";
                    
                    if (unvan.includes("ŞEF")) { borderColor = "#10b981"; icon = "🎖️"; }
                    else if (unvan.includes("MÜHENDİS")) { borderColor = "#10b981"; icon = "📐"; }
                    else if (unvan.includes("YÖNETMEN")) { borderColor = "#8b5cf6"; icon = "🎯"; }
                    else if (unvan.includes("UZMAN")) { borderColor = "#6366f1"; icon = "💡"; }

                    const namesList = d.data.names.map(name => `<div style="padding: 4px; border-bottom: 1px dashed #e2e8f0;">${name}</div>`).join('');
                        
                    return `
                    <div style="font-family: 'Inter', sans-serif; background-color: white; border: 1px solid #cbd5e1; border-radius: 12px; width: ${d.width}px; height: ${d.height}px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); padding: 12px; box-sizing: border-box; display: flex; flex-direction: column; align-items: center; border-left: 6px solid ${borderColor};">
                        
                        <div style="font-size: 13px; font-weight: 800; color: #0f172a; text-align: center; margin-bottom: 8px; width: 100%; display: flex; align-items: center; justify-content: center; gap: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${d.data.positionName}">
                            ${icon} ${d.data.positionName}
                            <span style="font-size: 11px; background: #f1f5f9; padding: 2px 6px; border-radius: 10px; border: 1px solid #cbd5e1;">${d.data.count}</span>
                        </div>
                        
                        <div class="group-scroll" onwheel="event.stopPropagation()" style="flex: 1; width: 100%; overflow-y: auto; background: #f8fafc; border-radius: 6px; padding: 4px; font-size: 12px; font-weight: 600; color: #475569; text-align: center; border: 1px solid #e2e8f0; line-height: 1.4; pointer-events: auto;">
                            ${namesList}
                        </div>
                    </div>`;
                }
            })
            .render();
            
        chart.expandAll();
        chart.fit();
    </script>
</body>
</html>
"""

json_str = json.dumps(root_data, ensure_ascii=False)
base64_encoded = base64.encodebytes(json_str.encode('utf-8')).decode('utf-8')
html_content = html_template.replace("JSON_PLACEHOLDER", base64_encoded)

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"{output_file} başarıyla oluşturuldu!")
