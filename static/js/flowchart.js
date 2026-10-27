/**
 * DisasterShield — Flowchart Visualization Engine
 * Renders hierarchical decision tree levels and handles Mermaid export.
 */

const FlowchartViewer = {
  currentDisaster: 'earthquake',

  init() {
    const selectElem = document.getElementById('flowchartDisasterSelect');
    const copyBtn = document.getElementById('btnCopyMermaid');

    if (selectElem) {
      selectElem.addEventListener('change', (e) => {
        this.currentDisaster = e.target.value;
        this.loadFlowchart(this.currentDisaster);
      });
    }

    if (copyBtn) {
      copyBtn.addEventListener('click', () => {
        const codePre = document.getElementById('mermaidCodePre');
        if (codePre) {
          navigator.clipboard.writeText(codePre.textContent).then(() => {
            if (window.showToast) window.showToast('Mermaid diagram code copied to clipboard!');
          });
        }
      });
    }

    // Initial load
    this.loadFlowchart(this.currentDisaster);
  },

  async loadFlowchart(disasterId) {
    const treeWrapper = document.getElementById('treeVisualWrapper');
    const codePre = document.getElementById('mermaidCodePre');
    const selectElem = document.getElementById('flowchartDisasterSelect');

    if (selectElem) selectElem.value = disasterId;
    this.currentDisaster = disasterId;

    if (treeWrapper) {
      treeWrapper.innerHTML = '<div style="padding: 2rem; text-align: center; color: #64748b;">Loading decision tree data...</div>';
    }

    try {
      const response = await fetch(`/api/flowchart/${disasterId}`);
      const data = await response.json();

      if (data.status === 'success') {
        if (codePre) codePre.textContent = data.mermaid;
        this.renderVisualTree(data.graph);
      } else {
        if (treeWrapper) treeWrapper.innerHTML = `<div style="color: #dc2626; padding: 1rem;">Failed to load flowchart: ${data.message}</div>`;
      }
    } catch (err) {
      console.error('Flowchart fetch error:', err);
      if (treeWrapper) treeWrapper.innerHTML = '<div style="color: #dc2626; padding: 1rem;">Network error fetching flowchart.</div>';
    }
  },

  renderVisualTree(graph) {
    const treeWrapper = document.getElementById('treeVisualWrapper');
    if (!treeWrapper) return;

    treeWrapper.innerHTML = '';

    // Group nodes by step level
    const stepGroups = { 1: [], 2: [], 3: [], 4: [] };
    const edgesByFrom = {};

    graph.edges.forEach(edge => {
      if (!edgesByFrom[edge.from]) edgesByFrom[edge.from] = [];
      edgesByFrom[edge.from].push(edge);
    });

    graph.nodes.forEach(node => {
      const step = node.step || 1;
      if (!stepGroups[step]) stepGroups[step] = [];
      stepGroups[step].push(node);
    });

    const stepTitles = {
      1: "Step 1: Initial Situation Assessment (Location & Setting)",
      2: "Step 2: Threat Severity & Physical State Evaluation",
      3: "Step 3: Secondary Hazard & Structural Hazard Assessment",
      4: "Step 4: Terminal Life-Safety Action Protocols & Guidance"
    };

    for (let step = 1; step <= 4; step++) {
      const nodesInStep = stepGroups[step] || [];
      if (nodesInStep.length === 0) continue;

      const levelBlock = document.createElement('div');
      levelBlock.className = 'tree-level-block';

      const levelTitle = document.createElement('h4');
      levelTitle.className = 'tree-level-title';
      levelTitle.textContent = stepTitles[step] || `Step ${step}`;
      levelBlock.appendChild(levelTitle);

      const nodesRow = document.createElement('div');
      nodesRow.className = 'tree-nodes-row';

      nodesInStep.forEach(node => {
        const card = document.createElement('div');
        let cardTypeClass = 'question';
        if (node.is_root) cardTypeClass = 'root';
        else if (node.is_terminal) {
          const sev = (node.urgency || '').toLowerCase();
          if (sev === 'critical') cardTypeClass = 'critical';
          else if (sev === 'urgent') cardTypeClass = 'urgent';
          else cardTypeClass = 'normal';
        }

        card.className = `tree-node-card ${cardTypeClass}`;

        const nodeId = document.createElement('span');
        nodeId.className = 'tree-node-id';
        nodeId.textContent = `Node: ${node.id} ${node.is_terminal ? '• [Terminal Guidance]' : ''}`;
        card.appendChild(nodeId);

        const nodeLabel = document.createElement('div');
        nodeLabel.className = 'tree-node-label';
        nodeLabel.textContent = node.label;
        card.appendChild(nodeLabel);

        // Append outgoing branches if not terminal
        if (!node.is_terminal && edgesByFrom[node.id]) {
          const branchesList = document.createElement('div');
          branchesList.className = 'tree-branches-list';

          edgesByFrom[node.id].forEach(branch => {
            const branchLink = document.createElement('div');
            branchLink.className = 'tree-branch-link';
            branchLink.innerHTML = `
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
              <span><strong>"${branch.label}"</strong> &rarr; ${branch.to}</span>
            `;
            branchesList.appendChild(branchLink);
          });

          card.appendChild(branchesList);
        }

        nodesRow.appendChild(card);
      });

      levelBlock.appendChild(nodesRow);
      treeWrapper.appendChild(levelBlock);
    }
  }
};

window.FlowchartViewer = FlowchartViewer;
