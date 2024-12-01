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
};

async function selectGame() {
    const selectedGame = document.getElementById('game-select').value;

    try {
        const response = await fetch(`/select_game?game=${encodeURIComponent(selectedGame)}`);

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        console.log('Game selected and data.json updated');
        await calculateTableList();
        attachEventListeners();
    } catch (error) {
        console.error('Error selecting game:', error);
    }
}
