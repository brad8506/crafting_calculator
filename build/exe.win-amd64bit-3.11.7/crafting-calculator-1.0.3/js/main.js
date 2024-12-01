// main.js

async function calculateTableList() {
    try {
        const response = await fetch('data.json');
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        const tableBody = document.getElementById('js-data-table-list');
        tableBody.innerHTML = '';

        function createTableRow(item, depth = 0, parentQuantity = 1) {
            const indent = ' '.repeat(depth * 4);  // Indentation for nested rows
            const rarityClass = item.rarity ? `rarity-${item.rarity.toLowerCase()}` : '';  // Class for rarity
            const depthClass = `depth-${depth}`;
            const subTableDepthClass = `depth-${depth + 1}`;
            const source = item.source || '';
            const wiki = item.wiki || '';

            const itemQuantity = item.quantity || 1;
            const calculatedQuantity = itemQuantity * parentQuantity;

            let rowHtml = `<tr class="${item.items ? 'expandable-row' : 'no-expand'} ${rarityClass} ${depthClass}" style="margin-left: ${indent};">`;
            rowHtml += item.items
                ? `<td class="item-name parent width30" onclick="toggleSubTable(this)" data-source="${source}" data-wiki="${wiki}">
                        <span class="expand-icon">+</span>${item.name}
                    </td>`
                : `<td class="item-name ${rarityClass} width30" data-source="${source}" data-wiki="${wiki}">${item.name}</td>`;

            const disabledAttr = depth > 0 ? 'disabled="disabled"' : '';
            rowHtml += `<td class="quantity"><input type="text" size="4" ${disabledAttr} data-quantity-original="${itemQuantity}" value="${calculatedQuantity}"/></td>`;

            if (depth === 0) {
                rowHtml += `<td class="output-wrapper"><textarea class="output" rows="1" cols="50"></textarea></td>`;
            }

            rowHtml += `</tr>`;

            if (item.items) {
                rowHtml += `<tr class="sub-table-row collapse" style="display: none;">
                            <td colspan="3">
                                <table class="sub-table ${subTableDepthClass}">
                                    <tr class="table-header-row"><th class="sub-item">Sub-Item</th><th class="quantity-required">Quantity Required</th></tr>`;
                for (const subItem in item.items) {
                    rowHtml += createTableRow(item.items[subItem], depth + 1, calculatedQuantity);
                }
                rowHtml += `</table></td></tr>`;
            }

            return rowHtml;
        }

        for (const key in data) {
            tableBody.innerHTML += createTableRow(data[key]);
        }

        attachEventListeners();
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

function toggleSubTable(element) {
    const icon = element.querySelector('.expand-icon');
    const row = element.closest('tr');
    const subTableRow = row.nextElementSibling;
    const outputWrapperTextarea = row.querySelector('.output-wrapper textarea');

    if (subTableRow.style.display === 'none') {
        subTableRow.style.display = '';
        icon.textContent = '-';
    } else {
        subTableRow.style.display = 'none';
        icon.textContent = '+';
    }

    if (outputWrapperTextarea) {
        outputWrapperTextarea.removeAttribute('style');
    }
}

function attachEventListeners() {
    const quantityInputs = document.querySelectorAll('.quantity input');

    quantityInputs.forEach(input => {
        input.removeEventListener('focus', updateOutput);
        input.removeEventListener('change', updateOutput);
        input.addEventListener('focus', updateOutput);
        input.addEventListener('change', updateOutput);
    });
}

function loadAndAttachListeners() {
    selectGame().then(() => {
        return calculateTableList();
    }).then(() => {
        attachEventListeners();
    });
}

function attachEventListeners() {
    const quantityInputs = document.querySelectorAll('.quantity input');

    // Remove any previously attached event listeners (optional, but good practice)
    quantityInputs.forEach(input => {
        input.removeEventListener('focus', updateOutput);
        input.removeEventListener('change', updateOutput);
    });

    // Attach new event listeners
    quantityInputs.forEach(input => {
        input.addEventListener('focus', updateOutput);
        input.addEventListener('change', updateOutput);
    });
}

function updateOutput(event) {
    const input = event.target;
    const row = input.closest('tr');
    const subTableRow = row.nextElementSibling;

    if (subTableRow && subTableRow.classList.contains('sub-table-row')) {
        const subTable = subTableRow.querySelector('.sub-table');
        const subItems = subTable.querySelectorAll('tr.expandable-row, tr.no-expand');

        // Retrieve the original quantity from the input field's parent row
        const originalQuantity = parseInt(row.querySelector('.quantity').getAttribute('data-quantity-original') || 1);
        const newQuantity = parseInt(input.value || 1);
        const multiplicationFactor = newQuantity / originalQuantity;

        let gatherItems = [];
        let craftItems = [];

        subItems.forEach(subItemRow => {
            const subItemNameElement = subItemRow.querySelector('.item-name');
            let subItemName = subItemNameElement ? subItemNameElement.textContent.trim() : 'Unknown Item';

            // Remove leading '+' or '-' character if present
            subItemName = subItemName.replace(/^[+-]/, '').trim();

            const subItemQuantityInput = subItemRow.querySelector('.quantity input');
            const subItemOriginalQuantity = parseInt(subItemQuantityInput.value || 1);
            const adjustedQuantity = subItemOriginalQuantity * newQuantity; // Adjust quantity based on the factor

            if (subItemRow.classList.contains('expandable-row')) {
                // Add to craft items group
                const rarityClass = [...subItemRow.classList].find(cls => cls.startsWith('rarity-'));
                const rarity = rarityClass ? `rarity: ${rarityClass.split('-')[1]}` : ''; // Extract rarity from class, e.g., 'rarity-green' becomes 'rarity: green'
                const source = subItemNameElement.dataset.source || ''
                const wiki = subItemNameElement.dataset.wiki || ''
                craftItems.push(` - ${subItemName}: ${adjustedQuantity}${rarity ? ', ' + rarity : ''}${source ? ', source: ' + source : ''}${wiki ? ', wiki: ' + wiki : ''}`);
            } else if (subItemRow.classList.contains('no-expand')) {
                // Add to gather items group
                const rarityClass = [...subItemRow.classList].find(cls => cls.startsWith('rarity-'));
                const rarity = rarityClass ? `rarity: ${rarityClass.split('-')[1]}` : ''; // Extract rarity from class, e.g., 'rarity-green' becomes 'rarity: green'
                const source = subItemNameElement.dataset.source || ''
                const wiki = subItemNameElement.dataset.wiki || ''
                gatherItems.push(` - ${subItemName}: ${adjustedQuantity}${rarity ? ', ' + rarity : ''}${source ? ', source: ' + source : ''}${wiki ? ', wiki: ' + wiki : ''}`);
            }
        });

        // Sort the items alphabetically
        gatherItems.sort();
        craftItems.sort();

        let toCraftItem = row.querySelector('.item-name').textContent.trim()
        // Remove leading '+' or '-' character if present.
        toCraftItem = toCraftItem.replace(/^[+-]/, '').trim();

        const toCraftQuantity = row.querySelector('.quantity input').value;
        const toCraftText = `To craft:\n${toCraftItem}: ${toCraftQuantity}`;
        const gatherItemsText = `Gather these items:\n${gatherItems.join('\n')}`;
        const craftItemsText = `Craft these intermediate items:\n${craftItems.join('\n')}`;

        const outputTextarea = row.querySelector('.output');
        if (outputTextarea) {
            outputTextarea.value = `${toCraftText}\n\n${gatherItemsText}\n\n${craftItemsText}`;
            // Auto-size the textarea
            outputTextarea.style.height = 'auto'; // Reset height
            outputTextarea.style.height = `${outputTextarea.scrollHeight}px`; // Set height based on content
        }
    }
}
