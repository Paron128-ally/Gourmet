let allRecipes = [];
let favorites = JSON.parse(localStorage.getItem('favorites')) || [];
let currentFilter = 'all';
let currentRecipe = null;
let currentOffset = 0;
const ALL_RECIPES_LIMIT = 1000;

function mapRecipe(recipe) {
  return {
    id: recipe.id,
    name: recipe.title || recipe.name || 'Untitled Recipe',
    image: recipe.image || '/icons/ingredients.jpg',
    cuisine: Array.isArray(recipe.cuisines) && recipe.cuisines.length ? recipe.cuisines[0] : recipe.cuisine || 'Global',
    time: recipe.readyInMinutes ? `${recipe.readyInMinutes} min` : (recipe.time || '30 min'),
    servings: recipe.servings ? `${recipe.servings}` : (recipe.servings || '4'),
    difficulty: recipe.dishTypes && recipe.dishTypes.length ? recipe.dishTypes[0] : (recipe.difficulty || 'Medium'),
    rating: recipe.spoonacularScore ? Math.round((recipe.spoonacularScore / 20) * 10) / 10 : (recipe.rating || 4.5),
    description: recipe.summary ? recipe.summary.replace(/<[^>]*>/g, '') : (recipe.description || 'Delicious recipe'),
    ingredients: Array.isArray(recipe.extendedIngredients)
      ? recipe.extendedIngredients.map(ing => ing.original || ing.name || '')
      : (Array.isArray(recipe.ingredients) ? recipe.ingredients : []),
    instructions: Array.isArray(recipe.analyzedInstructions) && recipe.analyzedInstructions.length
      ? recipe.analyzedInstructions[0].steps.map(step => step.step)
      : (Array.isArray(recipe.instructions) ? recipe.instructions : []),
    difficultyTag: recipe.dishTypes && recipe.dishTypes.length ? recipe.dishTypes[0] : (recipe.difficulty || 'Medium'),
  };
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
  loadRecipes();
  updateFavoritesCount();
  setupSearch();
});

function loadMore() {
  currentOffset += ALL_RECIPES_LIMIT;
  fetch(`/api/recipes?limit=${ALL_RECIPES_LIMIT}&offset=${currentOffset}`)
        .then(res => res.json())
        .then(data => {
            const newRecipes = data.recipes.map(mapRecipe);  // your existing mapping
            allRecipes = [...allRecipes, ...newRecipes];
            displayRecipes('all-recipes', allRecipes);
        });
}

    function loadRecipes() {
  currentOffset = 0;
  fetch(`/api/recipes?limit=${ALL_RECIPES_LIMIT}`)
        .then(res => res.json())
        .then(data => {
            if (Array.isArray(data.recipes) && data.recipes.length) {
                allRecipes = data.recipes.map(mapRecipe);  // store API results
            }
        })
        .catch(() => {
            console.warn('Could not load recipes from API.');
        })
        .finally(() => {
            displayRecipes('featured-recipes', allRecipes.slice(0, 6));
            displayRecipes('all-recipes', allRecipes);
        });
}

    function displayRecipes(containerId, recipes) {
      const container = document.getElementById(containerId);
      if (recipes.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-state-icon"><img src="/icons/eat.png" alt="No recipes found"></div><h3>No recipes found</h3><p>Try searching for something else</p></div>';
        return;
      }

      container.innerHTML = recipes.map(recipe => `
        <div class="recipe-card">
          <img src="${recipe.image}" alt="${recipe.name}" class="recipe-card-image">
          <div class="recipe-card-content">
            <button class="recipe-favorite-btn ${favorites.includes(recipe.id) ? 'favorited' : ''}" onclick="toggleFavorite(event, ${recipe.id})"><img src="/icons/heart.png" alt="Favorites"></button>
            <div class="recipe-card-title">${recipe.name}</div>
            <div class="recipe-card-meta">
              <span><img src="/icons/clock.png" alt="Time"> ${recipe.time}</span>
              <span><img src="/icons/people.png" alt="Servings"> ${recipe.servings}</span>
            </div>
            <div class="recipe-card-rating"><img src="/icons/star.png" alt="Rating"> ${recipe.rating}/5</div>
            <div class="recipe-card-description">${recipe.description}</div>
            <div class="recipe-card-footer">
              <button class="btn-primary" onclick="openModal(${recipe.id})">View Recipe</button>
              <button class="btn-secondary" onclick="toggleFavorite(event, ${recipe.id})">${favorites.includes(recipe.id) ? '<img src="/icons/heart.png" alt="Favorites"> Saved' : 'Save'}</button>
            </div>
          </div>
        </div>
      `).join('');
    }

    function openModal(recipeId) {
      currentRecipe = allRecipes.find(r => r.id === recipeId);
      const modal = document.getElementById('recipe-modal');
      const isFavorited = favorites.includes(recipeId);

      document.getElementById('modal-image').src = currentRecipe.image;
      document.getElementById('modal-title').textContent = currentRecipe.name;
      document.getElementById('modal-time').textContent = currentRecipe.time;
      document.getElementById('modal-servings').textContent = currentRecipe.servings;
      document.getElementById('modal-difficulty').textContent = currentRecipe.difficulty;
      document.getElementById('modal-rating').innerHTML = `<img src="/icons/star.png" alt="Rating"> ${currentRecipe.rating}/5`;
      
      const btn = document.getElementById('modal-favorite-btn');
      btn.innerHTML = isFavorited ? '<img src="/icons/heart.png" alt="Favorites"> Remove from Favorites' : '<img src="/icons/heart.png" alt="Favorites"> Add to Favorites';
      btn.classList.toggle('favorited', isFavorited);

      document.getElementById('modal-ingredients').innerHTML = currentRecipe.ingredients.map(ing => `<li>${ing}</li>`).join('');
      document.getElementById('modal-instructions').innerHTML = currentRecipe.instructions.map(inst => `<li>${inst}</li>`).join('');

      modal.classList.add('active');
    }

    function closeModal() {
      document.getElementById('recipe-modal').classList.remove('active');
    }

    function toggleFavorite(event, recipeId) {
      event.stopPropagation();
      const index = favorites.indexOf(recipeId);
      if (index > -1) {
        favorites.splice(index, 1);
      } else {
        favorites.push(recipeId);
      }
      localStorage.setItem('favorites', JSON.stringify(favorites));
      updateFavoritesCount();
      // Re-render from the recipes already loaded in memory instead of
      // re-fetching everything from the server just to flip one heart icon.
      displayRecipes('featured-recipes', allRecipes.slice(0, 6));
      displayRecipes('all-recipes', currentFilter === 'all' ? allRecipes : allRecipes.filter(r => r.cuisine === currentFilter));
    }

    function toggleFavoriteFromModal() {
      if (currentRecipe) {
        toggleFavorite({stopPropagation: () => {}}, currentRecipe.id);
        openModal(currentRecipe.id);
      }
    }

    function updateFavoritesCount() {
      document.getElementById('favorites-count').textContent = favorites.length;
    }

    function filterRecipes(eventOrCuisine, maybeCuisine) {
      const cuisine = typeof eventOrCuisine === 'string' ? eventOrCuisine : maybeCuisine;
      const event = typeof eventOrCuisine === 'string' ? null : eventOrCuisine;

      currentFilter = cuisine || 'all';
      const filtered = currentFilter === 'all' ? allRecipes : allRecipes.filter(r => r.cuisine === currentFilter);
      displayRecipes('all-recipes', filtered);

      document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.classList.remove('active');
      });
      if (event && event.target) {
        event.target.classList.add('active');
      }
    }

    function searchRecipes() {
      const query = document.getElementById('search-input').value.toLowerCase();
      const results = allRecipes.filter(recipe =>
        recipe.name.toLowerCase().includes(query) ||
        recipe.description.toLowerCase().includes(query) ||
        recipe.cuisine.toLowerCase().includes(query) ||
        recipe.ingredients.some(ing => ing.toLowerCase().includes(query))
      );
      
      showPage('recipes');
      displayRecipes('all-recipes', results);
    }

    function showPage(pageName) {
      document.querySelectorAll('.page-content').forEach(page => {
        page.classList.remove('active');
      });
      
      if (pageName === 'favorites') {
        const favoriteRecipes = allRecipes.filter(r => favorites.includes(r.id));
        displayRecipes('favorites-list', favoriteRecipes);
      }
      
      document.getElementById(pageName + '-content').classList.add('active');
      toggleSidebar();
    }

    function toggleSidebar() {
      const sidebar = document.getElementById('sidebar');
      const overlay = document.getElementById('overlay');
      sidebar.classList.toggle('active');
      overlay.classList.toggle('active');
    }

    function setupSearch() {
      const input = document.getElementById('search-input');
      input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
          searchRecipes();
        }
      });
    }

    document.getElementById('overlay').addEventListener('click', toggleSidebar);