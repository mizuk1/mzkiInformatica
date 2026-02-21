// Cursos page filtering and pagination

const COURSES_PER_PAGE = 9;
let currentPage = 1;
let filteredCourses = [];

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const filterApp = document.getElementById('filterApp');
    const filterNivel = document.getElementById('filterNivel');
    const filterVersao = document.getElementById('filterVersao');
    const clearFiltersBtn = document.getElementById('clearFilters');
    const searchBtn = document.getElementById('searchBtn');
    const appCards = document.querySelectorAll('.app-card');
    const courseCount = document.getElementById('courseCount');
    
    // Ensure allCourses is defined (passed from template)
    if (typeof allCourses === 'undefined') {
        console.warn('allCourses data not found');
        return;
    }
    
    // Ler parâmetros da URL
    const urlParams = new URLSearchParams(window.location.search);
    const appFromUrl = urlParams.get('app');
    
    function filterAndRender() {
        const searchTerm = searchInput.value.toLowerCase();
        const appFilter = filterApp.value;
        const nivelFilter = filterNivel.value;
        const versaoFilter = filterVersao.value;
        
        // Filtrar cursos
        filteredCourses = allCourses.filter(curso => {
            const matchSearch = searchTerm === '' || 
                               curso.titulo.toLowerCase().includes(searchTerm) || 
                               curso.app.toLowerCase().includes(searchTerm);
            const matchApp = appFilter === '' || curso.app === appFilter;
            const matchNivel = nivelFilter === '' || curso.nivel === nivelFilter;
            const matchVersao = versaoFilter === '' || curso.versao === versaoFilter;
            
            return matchSearch && matchApp && matchNivel && matchVersao;
        });
        
        // Resetar para primeira página
        currentPage = 1;
        
        // Atualizar UI
        renderPage();
        renderPagination();
    }
    
    function renderPage() {
        const grid = document.getElementById('coursesGrid');
        grid.innerHTML = '';
        
        if (filteredCourses.length === 0) {
            const section = document.querySelector('section.py-4.py-xl-5');
            if (section) {
                section.innerHTML = `
                    <div class="container">
                        <div class="text-center py-5">
                            <p class="text-muted fs-5">😔 Nenhum curso encontrado com os filtros selecionados.</p>
                            <button id="clearFiltersBtn2" class="btn btn-primary">Limpar filtros</button>
                        </div>
                    </div>
                `;
                const clearBtn2 = document.getElementById('clearFiltersBtn2');
                if (clearBtn2) {
                    clearBtn2.addEventListener('click', clearAllFilters);
                }
            }
            document.getElementById('courseCount').textContent = '0';
            return;
        }
        
        // Calcular índices de início e fim
        const startIdx = (currentPage - 1) * COURSES_PER_PAGE;
        const endIdx = startIdx + COURSES_PER_PAGE;
        const pageCourses = filteredCourses.slice(startIdx, endIdx);
        
        // Renderizar cursos
        pageCourses.forEach(curso => {
            const col = document.createElement('div');
            col.className = 'col-12 col-md-6 col-lg-4';
            col.innerHTML = `
                <div class="card h-100 border-0 shadow-sm overflow-hidden">
                    <div style="height: 5px; background-color: ${curso.cor};"></div>
                    <div class="card-body p-4 d-flex flex-column">
                        <span class="badge text-white mb-3 align-self-start" style="background-color: ${curso.cor};">${curso.app}</span>
                        <h5 class="card-title fw-bold mb-2">${curso.titulo}</h5>
                        <p class="text-muted small mb-3">${curso.nivel} • ${curso.versao} • ${curso.carga_horaria}</p>
                        <p class="text-muted small mb-3">
                            ${curso.modalidades && curso.modalidades.length > 0 
                                ? '<strong>Modalidades:</strong> ' + curso.modalidades.map(m => m.nome).join(', ')
                                : 'Modalidade não especificada'
                            }
                        </p>
                        <p class="card-text text-muted small flex-grow-1 lh-sm">${curso.descricao_curta.substring(0, 100)}...</p>
                        <a href="/cursos/${curso.id}/" class="btn btn-sm mt-3 w-100" style="background-color: ${curso.cor}; color: white; border: none;">
                            Ver detalhes
                        </a>
                    </div>
                </div>
            `;
            grid.appendChild(col);
        });
        
        // Atualizar contador
        document.getElementById('courseCount').textContent = filteredCourses.length;
    }
    
    function renderPagination() {
        const paginationList = document.getElementById('paginationList');
        paginationList.innerHTML = '';
        
        if (filteredCourses.length <= COURSES_PER_PAGE) {
            document.getElementById('paginationNav').style.display = 'none';
            return;
        }
        
        document.getElementById('paginationNav').style.display = 'block';
        
        const numPages = Math.ceil(filteredCourses.length / COURSES_PER_PAGE);
        
        // Botão Anterior
        if (currentPage > 1) {
            const li = document.createElement('li');
            li.className = 'page-item';
            li.innerHTML = '<a class="page-link" href="#">Anterior</a>';
            li.addEventListener('click', (e) => {
                e.preventDefault();
                currentPage--;
                renderPage();
                renderPagination();
            });
            paginationList.appendChild(li);
        }
        
        // Números das páginas
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(numPages, currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            const li = document.createElement('li');
            li.className = i === currentPage ? 'page-item active' : 'page-item';
            const tag = i === currentPage ? 'span' : 'a';
            const activeClass = i === currentPage ? ' active' : '';
            li.className = `page-item${activeClass}`;
            li.innerHTML = `<${tag} class="page-link" ${i !== currentPage ? 'href="#"' : ''}>${i}</${tag}>`;
            if (i !== currentPage) {
                li.querySelector('a').addEventListener('click', (e) => {
                    e.preventDefault();
                    currentPage = i;
                    renderPage();
                    renderPagination();
                });
            }
            paginationList.appendChild(li);
        }
        
        // Botão Próxima
        if (currentPage < numPages) {
            const li = document.createElement('li');
            li.className = 'page-item';
            li.innerHTML = '<a class="page-link" href="#">Próxima</a>';
            li.addEventListener('click', (e) => {
                e.preventDefault();
                currentPage++;
                renderPage();
                renderPagination();
            });
            paginationList.appendChild(li);
        }
    }
    
    function clearAllFilters() {
        searchInput.value = '';
        filterApp.value = '';
        filterNivel.value = '';
        filterVersao.value = '';
        filterAndRender();
    }

    function scrollToCoursesOnSmallScreens() {
        if (window.innerWidth < 768) {
            setTimeout(() => {
                const coursesGrid = document.getElementById('coursesGrid');
                if (coursesGrid) {
                    coursesGrid.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 100);
        }
    }
    
    // Event listeners
    if (searchInput) searchInput.addEventListener('input', filterAndRender);
    if (filterApp) filterApp.addEventListener('change', filterAndRender);
    if (filterNivel) filterNivel.addEventListener('change', filterAndRender);
    if (filterVersao) filterVersao.addEventListener('change', filterAndRender);
    if (clearFiltersBtn) clearFiltersBtn.addEventListener('click', clearAllFilters);
    if (searchBtn) {
        searchBtn.addEventListener('click', (e) => {
            e.preventDefault();
            filterAndRender();
            scrollToCoursesOnSmallScreens();
        });
    }
    
    // Botões do app showcase
    appCards.forEach(card => {
        card.addEventListener('click', function(e) {
            e.preventDefault();
            const app = this.getAttribute('data-app');
            filterApp.value = app;
            searchInput.value = '';
            filterNivel.value = '';
            filterVersao.value = '';
            filterAndRender();
            
            scrollToCoursesOnSmallScreens();
        });
    });
    
    // Aplicar filtro de app se vindo da home page
    if (appFromUrl) {
        filterApp.value = appFromUrl;
    }
    
    // Renderizar inicial
    filterAndRender();
});
