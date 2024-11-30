// game.js

window.onload = function() {
    fetch('/discover_games')
        .then(response => response.json())
        .then(games => {
            const select = document.getElementById('game-select');
            games.forEach(game => {
                const option = document.createElement('option');
                option.value = game;
                option.text = game;
                select.add(option);
            });
        })
        .catch(error => console.error('Error discovering games:', error));

    // Add event listener for specialization dropdown change (if applicable)
    const selectBox = document.getElementById('specialisation-select');
    selectBox.addEventListener('change', function() {
        const selectedSpecialisation = this.value;
        if (selectedSpecialisation && selectedSpecialisation.trim() !== '') {
            setQueryStringParameter('specialisation', selectedSpecialisation)
            filterRecipesBySpecialization(selectedSpecialisation);
        }
    });
    const changeEvent = new Event('change');
    selectBox.dispatchEvent(changeEvent);

    const { game, specialisation } = getQueryParams();
    if (game && specialisation) {
        document.getElementById('game-select').value = game;
        document.getElementById('specialisation-select').value = specialisation;
        filterRecipes();  // Automatically filter when the page loads with query params
    }

    loadGamesAndSpecialisations();
};

async function selectGame() {
    const selectedGame = document.getElementById('game-select').value;

    try {
        const response = await fetch(`/select_game?game=${encodeURIComponent(selectedGame)}`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        console.log('Game selected and data.json updated');

        // Fetch and populate specializations
        await fetchSpecialisations(selectedGame);

        await calculateTableList();
        attachEventListeners();
    } catch (error) {
        console.error('Error selecting game:', error);
    }
}

async function fetchSpecialisations(game) {
    try {
        const response = await fetch(`/discover_specialisations?game=${encodeURIComponent(game)}`);
        if (!response.ok) {
            throw new Error('Failed to fetch specialisations');
        }

        const specialisations = await response.json();
        const specialisationSelect = document.getElementById('specialisation-select');
        specialisationSelect.innerHTML = ''; // Clear existing options

        specialisations.forEach(specialisation => {
            const option = document.createElement('option');
            option.value = specialisation;
            option.text = specialisation;
            specialisationSelect.add(option);
        });

        console.log('Specialisations loaded:', specialisations);
    } catch (error) {
        console.error('Error fetching specialisations:', error);
    }
}

function filterRecipesBySpecialization(specialisation = '') {
    const game = new URLSearchParams(window.location.search).get('game');
    const urlSpecialisation = new URLSearchParams(window.location.search).get('specialisation');

    // Use the specialisation from the URL if not passed in as an argument
    const effectiveSpecialisation = specialisation || urlSpecialisation;
    const url = `/filter_recipes/${game}/${effectiveSpecialisation}`;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            // Handle the filtered recipe data (display, etc.)
            console.log('Filtered recipes:', data);
            // Assuming you have a function to display or process the data
            calculateTableList();
            attachEventListeners();
        })
        .catch(error => {
            console.error('Error fetching filtered recipes:', error);
        });
}

function getQueryParams() {
    const queryParams = new URLSearchParams(window.location.search);
    return {
        game: queryParams.get('game'),
        specialisation: queryParams.get('specialisation')
    };
}

function setQueryStringParameter(key, value) {
    const url = new URL(window.location.href);
    url.searchParams.set(key, value);
    window.history.replaceState({}, '', url);
}
