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
            let style = [];
            if (depth > 0) {
                const indent = ' '.repeat((depth) * 4); // Indentation for nested rows
                style.push(`margin-left: ${indent}`)
            }

            if (style.length > 0) {
                // Implode style array to a string.
                style = style.join(';');
            } else {
                style = ''
            }

            const rarityClass = item.rarity ? `rarity-${item.rarity.toLowerCase()}` : '';  // Class for rarity
            const depthClass = `depth-${depth}`;
            const subTableDepthClass = `depth-${depth + 1}`;
            const source = item.source || '';
            const wiki = item.wiki || '';

            const itemQuantity = item.quantity || 1;
            const calculatedQuantity = itemQuantity * parentQuantity;

            let rowHtml = `<tr class="${item.items ? 'expandable-row' : 'no-expand'} ${rarityClass} ${depthClass}" ${style}>`;
            rowHtml += item.items
                ? `<td class="item-name parent width30" onclick="toggleSubTable(this)" data-source="${source}" data-wiki="${wiki}">
                        <span class="expand-icon">+</span>${item.name}
                    </td>`
                : `<td class="item-name ${rarityClass} width30" data-source="${source}" data-wiki="${wiki}">${item.name}</td>`;

            const disabledAttr = depth > 0 ? 'disabled="disabled"' : '';
            
            // td quantity start.
            rowHtml += `<td class="quantity">`;
            
            if (depth === 0) {
                rowHtml += `<button class="minus-btn">-</button>`
            }
            rowHtml += `<input class="quantity-input" type="text" size="4" ${disabledAttr} data-quantity-original="${itemQuantity}" value="${calculatedQuantity}"/>`
            
            if (depth === 0) {
                rowHtml += `<button class="plus-btn">+</button>`
            }
            
            rowHtml += `</td>`;
            // td quantity end.

            if (depth === 0) {
                rowHtml += `<td class="output-wrapper">`;
                rowHtml += `<button class="copy-btn">Copy</button>`;
                rowHtml += `<textarea class="output" rows="1" cols="50"></textarea>`;
                rowHtml += `</td>`;
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

function loadAndAttachListeners() {
    selectGame().then(() => {
        const selectedGame = document.getElementById('game-select').value;
        setQueryStringParameter('game', selectedGame);
        calculateTableList();

        // Show specialisation filter wrapper.
        const elements = document.getElementsByClassName('specialisation-wrapper');
        for (const element of elements) {
            element.style.display = 'block';
        }
    }).then(() => {
        attachEventListeners();
    });
}

// function loadGamesAndSpecialisations() {
//     // Fetch games and specialisations from server or static data
//     fetch('/discover_games')
//         .then(response => response.json())
//         .then(games => {
//             const gameSelect = document.getElementById('game-select');
//             games.forEach(game => {
//                 const option = document.createElement('option');
//                 option.value = game;
//                 option.textContent = game;
//                 gameSelect.appendChild(option);
//             });
//         });

//     // Fetch specialisations based on the selected game
//     const gameSelect = document.getElementById('game-select');
//     gameSelect.addEventListener('change', function() {
//         const selectedGame = gameSelect.value;
//         fetch(`/discover_specialisations?game=${selectedGame}`)
//             .then(response => response.json())
//             .then(specialisations => {
//                 const specialisationSelect = document.getElementById('specialisation-select');
//                 specialisationSelect.innerHTML = ''; // Clear current options
//                 specialisations.forEach(specialisation => {
//                     const option = document.createElement('option');
//                     option.value = specialisation;
//                     option.textContent = specialisation;
//                     specialisationSelect.appendChild(option);
//                 });
//             });
//     });
// }

function setQueryStringParameter(key, value) {
    const url = new URL(window.location.href);
    url.searchParams.set(key, value);
    window.history.replaceState({}, '', url);
}

// Clear a specific parameter
function clearQueryStringParameter(key) {
    const url = new URL(window.location.href);
    url.searchParams.delete(key);
    window.history.replaceState({}, '', url);
}

// Clear all parameters
function clearAllQueryStringParameters() {
    const url = new URL(window.location.href);
    url.search = '';
    window.history.replaceState({}, '', url);
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

    const quantityButtons = document.querySelectorAll('.plus-btn,.minus-btn');
    quantityButtons.forEach(input => {
        input.removeEventListener('click', processQuantityButtonClick);
        input.addEventListener('click', processQuantityButtonClick);
    });

    const copyButtons = document.getElementsByClassName("copy-btn");
    Array.from(copyButtons).forEach(button => {
        button.addEventListener("click", function () {
            // Get the text to copy
            const copyText = button.closest('tr').querySelector('.output');
            if (copyText) {
                copyText.select();
                copyText.setSelectionRange(0, 99999); // For mobile compatibility
                navigator.clipboard.writeText(copyText.value).then(() => {
                    // alert("Text copied to clipboard!");
                }).catch(err => {
                    console.error("Failed to copy text: ", err);
                });
            }
        });
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

        const gatherMap = new Map();
        const craftMap = new Map();

        subItems.forEach(subItemRow => {
            const subItemNameElement = subItemRow.querySelector('.item-name');
            let subItemName = subItemNameElement ? subItemNameElement.textContent.trim() : 'Unknown Item';

            // Remove leading '+' or '-' character if present
            subItemName = subItemName.replace(/^[+-]/, '').trim();

            const subItemQuantityInput = subItemRow.querySelector('.quantity input');
            const subItemOriginalQuantity = parseInt(subItemQuantityInput.value || 1);
            const adjustedQuantity = subItemOriginalQuantity * multiplicationFactor;

            const rarityClass = [...subItemRow.classList].find(cls => cls.startsWith('rarity-'));
            const rarity = rarityClass ? `rarity: ${rarityClass.split('-')[1]}` : '';
            const source = subItemNameElement.dataset.source || '';
            const wiki = subItemNameElement.dataset.wiki || '';
            const key = `${subItemName}|${rarity}|${source}|${wiki}`;

            const targetMap = subItemRow.classList.contains('expandable-row') ? craftMap : gatherMap;

            if (targetMap.has(key)) {
                targetMap.set(key, targetMap.get(key) + adjustedQuantity);
            } else {
                targetMap.set(key, adjustedQuantity);
            }
        });

        // Convert maps to sorted arrays
        const gatherItems = Array.from(gatherMap).map(([key, quantity]) => {
            const [name, rarity, source, wiki] = key.split('|');
            return ` - ${name}: ${quantity}${rarity ? `, ${rarity}` : ''}${source ? `, source: ${source}` : ''}${wiki ? `, wiki: ${wiki}` : ''}`;
        }).sort();

        const craftItems = Array.from(craftMap).map(([key, quantity]) => {
            const [name, rarity, source, wiki] = key.split('|');
            return ` - ${name}: ${quantity}${rarity ? `, ${rarity}` : ''}${source ? `, source: ${source}` : ''}${wiki ? `, wiki: ${wiki}` : ''}`;
        }).sort();

        let toCraftItem = row.querySelector('.item-name').textContent.trim();
        // Remove leading '+' or '-' character if present
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

            // Show the copy button
            const closestTableRow = outputTextarea.closest("tr");
            closestTableRow.querySelector('.copy-btn').style.display = "block";
        }
    }
}


function processQuantityButtonClick(event) {
    const button = event.target;

    // Check if the clicked element is either a plus or minus button
    if (button.classList.contains('plus-btn') || button.classList.contains('minus-btn')) {
        const input = button.closest('.quantity').querySelector('.quantity-input');
        let value = parseInt(input.value) || 0;

        // Handle the behavior based on the button type (plus or minus)
        if (button.classList.contains('plus-btn')) {
            input.value = value + 1;
        } else if (button.classList.contains('minus-btn') && value > 0) {
            input.value = value - 1;
        }
        const changeEvent = new Event('change');
        input.dispatchEvent(changeEvent);
    }
};
