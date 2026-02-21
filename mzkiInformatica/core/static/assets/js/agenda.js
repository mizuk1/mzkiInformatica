// Agenda page scripts - Month navigation and event loading

document.addEventListener('DOMContentLoaded', function() {
    // Variáveis para detectar swipe
    let touchStartX = 0;
    let touchEndX = 0;
    
    function carregarEventosMes(mes, ano) {
        const url = `?mes=${mes}&ano=${ano}`;
        const container = document.getElementById('eventos-mes-container');
        const spinner = document.getElementById('loading-spinner');
        
        // Mostrar spinner
        if (spinner) {
            spinner.classList.add('active');
        }
        
        // Fade out
        container.classList.add('fade-out');
        
        fetch(url)
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const novoConteudo = doc.querySelector('#eventos-mes-container');
                
                if (novoConteudo) {
                    // Atualizar conteúdo
                    container.innerHTML = novoConteudo.innerHTML;
                    
                    // Atualizar mes_nome nos cards
                    const novaMesDiv = doc.querySelector('#mes-nome-cards');
                    if (novaMesDiv) {
                        document.getElementById('mes-nome-cards').textContent = novaMesDiv.textContent;
                    }
                    
                    // Atualizar data-mes e data-ano dos botões
                    const newBtnAnterior = doc.getElementById('btn-eventos-anterior');
                    const newBtnProximo = doc.getElementById('btn-eventos-proximo');
                    const btnEventosAnterior = document.getElementById('btn-eventos-anterior');
                    const btnEventosProximo = document.getElementById('btn-eventos-proximo');
                    
                    if (newBtnAnterior && btnEventosAnterior) {
                        btnEventosAnterior.setAttribute('data-mes', newBtnAnterior.getAttribute('data-mes'));
                        btnEventosAnterior.setAttribute('data-ano', newBtnAnterior.getAttribute('data-ano'));
                    }
                    if (newBtnProximo && btnEventosProximo) {
                        btnEventosProximo.setAttribute('data-mes', newBtnProximo.getAttribute('data-mes'));
                        btnEventosProximo.setAttribute('data-ano', newBtnProximo.getAttribute('data-ano'));
                    }
                    
                    // Atualizar carousel de meses (para telas pequenas)
                    atualizarCarouselMeses(doc, mes, ano);
                    
                    // Fade in
                    setTimeout(() => {
                        container.classList.remove('fade-out');
                        container.classList.add('fade-in');
                        
                        // Remover spinner
                        if (spinner) {
                            spinner.classList.remove('active');
                        }
                        
                        // Re-adicionar event listeners aos botões
                        adicionarEventListenersEventos();
                        
                        // Remover classe fade-in após transição
                        setTimeout(() => {
                            container.classList.remove('fade-in');
                        }, 300);
                    }, 100);
                }
            })
            .catch(error => {
                console.error('Erro ao carregar eventos do mês:', error);
                if (spinner) {
                    spinner.classList.remove('active');
                }
                container.classList.remove('fade-out');
            });
    }
    
    function atualizarCarouselMeses(doc, mesAtual, anoAtual) {
        // Extrair dados do carousel do novo HTML
        const newCarouselPrev = doc.getElementById('carousel-prev');
        const newCarouselCurrent = doc.getElementById('carousel-current');
        const newCarouselNext = doc.getElementById('carousel-next');
        
        // Atualizar elementos do carousel no DOM atual
        const carouselPrev = document.getElementById('carousel-prev');
        const carouselCurrent = document.getElementById('carousel-current');
        const carouselNext = document.getElementById('carousel-next');
        
        if (carouselPrev && newCarouselPrev) {
            carouselPrev.setAttribute('data-mes', newCarouselPrev.getAttribute('data-mes'));
            carouselPrev.setAttribute('data-ano', newCarouselPrev.getAttribute('data-ano'));
            carouselPrev.innerHTML = newCarouselPrev.innerHTML;
        }
        
        if (carouselCurrent && newCarouselCurrent) {
            carouselCurrent.innerHTML = newCarouselCurrent.innerHTML;
        }
        
        if (carouselNext && newCarouselNext) {
            carouselNext.setAttribute('data-mes', newCarouselNext.getAttribute('data-mes'));
            carouselNext.setAttribute('data-ano', newCarouselNext.getAttribute('data-ano'));
            carouselNext.innerHTML = newCarouselNext.innerHTML;
        }
    }
    
    function handleAnterior(e) {
        e.preventDefault();
        const mes = this.getAttribute('data-mes');
        const ano = this.getAttribute('data-ano');
        carregarEventosMes(mes, ano);
    }
    
    function handleProximo(e) {
        e.preventDefault();
        const mes = this.getAttribute('data-mes');
        const ano = this.getAttribute('data-ano');
        carregarEventosMes(mes, ano);
    }
    
    function adicionarSwipeDetection() {
        const eventosContainer = document.getElementById('eventos-mes-container');
        if (!eventosContainer) return;
        
        eventosContainer.removeEventListener('touchstart', handleTouchStart);
        eventosContainer.removeEventListener('touchend', handleTouchEnd);
        
        eventosContainer.addEventListener('touchstart', handleTouchStart, false);
        eventosContainer.addEventListener('touchend', handleTouchEnd, false);
    }
    
    function handleTouchStart(e) {
        // Verificar se o toque foi em um card
        const target = e.target;
        const isCard = target.closest('.card') || target.closest('.col-md-6') || target.closest('.col-lg-4');
        
        if (!isCard) {
            touchStartX = e.changedTouches[0].screenX;
        } else {
            touchStartX = 0; // Resetar para evitar swipe em cards
        }
    }
    
    function handleTouchEnd(e) {
        // Verificar se o toque foi em um card
        const target = e.target;
        const isCard = target.closest('.card') || target.closest('.col-md-6') || target.closest('.col-lg-4');
        
        if (!isCard && touchStartX !== 0) {
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe();
        }
    }
    
    function handleSwipe() {
        const swipeThreshold = 50;
        const diff = touchStartX - touchEndX;
        
        // Swipe para esquerda (próximo mês)
        if (diff > swipeThreshold) {
            const btnProximo = document.getElementById('btn-eventos-proximo');
            if (btnProximo) {
                btnProximo.click();
            }
        }
        
        // Swipe para direita (mês anterior)
        if (diff < -swipeThreshold) {
            const btnAnterior = document.getElementById('btn-eventos-anterior');
            if (btnAnterior) {
                btnAnterior.click();
            }
        }
    }
    
    function adicionarEventListenersEventos() {
        const btnAnterior = document.getElementById('btn-eventos-anterior');
        const btnProximo = document.getElementById('btn-eventos-proximo');
        
        if (btnAnterior) {
            btnAnterior.removeEventListener('click', handleAnterior);
            btnAnterior.addEventListener('click', handleAnterior);
        }
        
        if (btnProximo) {
            btnProximo.removeEventListener('click', handleProximo);
            btnProximo.addEventListener('click', handleProximo);
        }
        
        // Adicionar listeners para carousel em telas pequenas
        adicionarCarouselListeners();
        
        // Adicionar detecção de swipe na seção de eventos
        adicionarSwipeDetection();
    }
    
    function adicionarCarouselListeners() {
        const carouselPrev = document.getElementById('carousel-prev');
        const carouselNext = document.getElementById('carousel-next');
        
        if (carouselPrev) {
            carouselPrev.removeEventListener('click', handleCarouselPrev);
            carouselPrev.addEventListener('click', handleCarouselPrev);
        }
        
        if (carouselNext) {
            carouselNext.removeEventListener('click', handleCarouselNext);
            carouselNext.addEventListener('click', handleCarouselNext);
        }
    }
    
    function handleCarouselPrev(e) {
        e.preventDefault();
        this.blur();
        const mes = this.getAttribute('data-mes');
        const ano = this.getAttribute('data-ano');
        carregarEventosMes(mes, ano);
    }
    
    function handleCarouselNext(e) {
        e.preventDefault();
        this.blur();
        const mes = this.getAttribute('data-mes');
        const ano = this.getAttribute('data-ano');
        carregarEventosMes(mes, ano);
    }
    
    // Inicializar event listeners
    adicionarEventListenersEventos();
});
