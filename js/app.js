// Data will be loaded from JSON files (converted from CSV)
// For GitHub Pages, we serve static JSON
let recipes = [];
let ingredients = [];
let selectedAilments = new Set();
let selectedIngredients = new Set();
let selectedCategories = new Set();
let selectedSources = new Set();

async function loadData() {
    const [recipesRes, ingredientsRes] = await Promise.all([
        fetch('data/recipes.json'),
        fetch('data/ingredients.json')
    ]);
    recipes = await recipesRes.json();
    ingredients = await ingredientsRes.json();
    buildFilters();
    renderRecipes();
}

function getUniqueAilments() {
    const ailments = new Set();
    recipes.forEach(r => {
        r.ailments.split('|').forEach(a => {
            if (a.trim()) ailments.add(a.trim());
        });
    });
    return [...ailments].sort();
}

function getUniqueIngredients() {
    const names = new Set();
    ingredients.forEach(i => names.add(i.ingredient));
    return [...names].sort();
}

function getUniqueCategories() {
    const cats = new Set();
    recipes.forEach(r => { if (r.category) cats.add(r.category); });
    return [...cats].sort();
}

function getUniqueSources() {
    const sources = new Set();
    recipes.forEach(r => {
        if (r.source_author && r.source_work) {
            sources.add(`${r.source_author} — ${r.source_work} (${r.source_year})`);
        }
    });
    return [...sources].sort();
}

function buildFilters() {
    buildDropdown('ailment', getUniqueAilments(), selectedAilments);
    buildDropdown('ingredient', getUniqueIngredients(), selectedIngredients);
    buildDropdown('category', getUniqueCategories(), selectedCategories);
    buildDropdown('source', getUniqueSources(), selectedSources);
}

function buildDropdown(type, items, selectedSet) {
    const list = document.getElementById(`${type}-list`);
    const search = document.getElementById(`${type}-search`);

    function renderItems(filter = '') {
        const filtered = items.filter(i => i.toLowerCase().includes(filter.toLowerCase()));
        list.innerHTML = filtered.map(item => `
            <div class="dropdown-item">
                <input type="checkbox" id="${type}-${item}" ${selectedSet.has(item) ? 'checked' : ''}>
                <label for="${type}-${item}">${item}</label>
            </div>
        `).join('');

        list.querySelectorAll('.dropdown-item').forEach(el => {
            const checkbox = el.querySelector('input');
            const label = el.querySelector('label').textContent;
            el.addEventListener('click', (e) => {
                if (e.target !== checkbox) checkbox.checked = !checkbox.checked;
                if (checkbox.checked) {
                    selectedSet.add(label);
                } else {
                    selectedSet.delete(label);
                }
                renderTags(type, selectedSet);
                renderRecipes();
            });
        });
    }

    search.addEventListener('focus', () => {
        list.classList.add('open');
        renderItems(search.value);
    });

    search.addEventListener('input', () => {
        renderItems(search.value);
    });

    document.addEventListener('click', (e) => {
        if (!e.target.closest(`#${type}-filter`)) {
            list.classList.remove('open');
        }
    });

    renderItems();
}

function renderTags(type, selectedSet) {
    const container = document.getElementById(`${type}-tags`);
    container.innerHTML = [...selectedSet].map(item => `
        <span class="tag">${item}<button data-type="${type}" data-value="${item}">&times;</button></span>
    `).join('');

    container.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', () => {
            selectedSet.delete(btn.dataset.value);
            renderTags(type, selectedSet);
            renderRecipes();
            // Uncheck in dropdown
            const checkbox = document.getElementById(`${type}-${btn.dataset.value}`);
            if (checkbox) checkbox.checked = false;
        });
    });
}

function getRecipeIngredients(recipeId) {
    return ingredients.filter(i => i.recipe_id === recipeId);
}

function filterRecipes() {
    return recipes.filter(recipe => {
        const recipeAilments = recipe.ailments.split('|').map(a => a.trim());
        const recipeIngredients = getRecipeIngredients(recipe.id).map(i => i.ingredient);
        const recipeSource = recipe.source_author && recipe.source_work ?
            `${recipe.source_author} — ${recipe.source_work} (${recipe.source_year})` : '';

        const ailmentMatch = selectedAilments.size === 0 ||
            [...selectedAilments].some(a => recipeAilments.includes(a));

        const ingredientMatch = selectedIngredients.size === 0 ||
            [...selectedIngredients].some(i => recipeIngredients.includes(i));

        const categoryMatch = selectedCategories.size === 0 ||
            selectedCategories.has(recipe.category);

        const sourceMatch = selectedSources.size === 0 ||
            selectedSources.has(recipeSource);

        return ailmentMatch && ingredientMatch && categoryMatch && sourceMatch;
    });
}

function renderRecipes() {
    const filtered = filterRecipes();
    document.getElementById('result-count').textContent = `Showing ${filtered.length} of ${recipes.length} recipes`;

    const container = document.getElementById('recipe-list');
    container.innerHTML = filtered.map(recipe => {
        const recipeIngredients = getRecipeIngredients(recipe.id);
        const ailments = recipe.ailments.split('|').map(a =>
            `<span class="ailment-badge">${a.trim()}</span>`
        ).join('');

        const ingredientRows = recipeIngredients.map(i => `
            <tr>
                <td>${i.ingredient}</td>
                <td>${i.quantity_metric || ''} ${i.unit_metric || ''}</td>
                <td>${i.quantity_imperial || ''} ${i.unit_imperial || ''}</td>
                <td>${i.notes || ''}</td>
            </tr>
        `).join('');

        const sourceLink = recipe.source_url ?
            `<a class="source-link" href="${recipe.source_url}" target="_blank">View original →</a>` : '';

        const instructions = recipe.instructions ?
            `<div class="recipe-instructions"><p>${recipe.instructions}</p></div>` : '';

        const notes = recipe.notes ?
            `<div class="recipe-notes"><p><em>${recipe.notes}</em></p></div>` : '';

        const attribution = recipe.source_author ?
            `<div class="recipe-source">
                <span class="source-author">${recipe.source_author}</span>,
                <span class="source-work"><em>${recipe.source_work}</em></span>
                (${recipe.source_year})
                — Digitized by ${recipe.digitized_by}
            </div>` : '';

        return `
            <div class="recipe-card">
                <span class="category">${recipe.category}</span>
                <h3>${recipe.name}</h3>
                <div class="ailments">${ailments}</div>
                ${instructions}
                ${notes}
                ${recipeIngredients.length ? `
                <div class="ingredients-list">
                    <h4>Ingredients</h4>
                    <table>
                        <tr><th>Ingredient</th><th>Metric</th><th>Imperial</th><th>Notes</th></tr>
                        ${ingredientRows}
                    </table>
                </div>` : ''}
                ${attribution}
                ${sourceLink}
            </div>
        `;
    }).join('');
}

// Clear filters
document.getElementById('clear-filters').addEventListener('click', () => {
    selectedAilments.clear();
    selectedIngredients.clear();
    selectedCategories.clear();
    selectedSources.clear();
    ['ailment', 'ingredient', 'category', 'source'].forEach(type => {
        document.getElementById(`${type}-tags`).innerHTML = '';
        document.getElementById(`${type}-search`).value = '';
    });
    document.querySelectorAll('.dropdown-item input[type="checkbox"]').forEach(cb => cb.checked = false);
    renderRecipes();
});

loadData();
