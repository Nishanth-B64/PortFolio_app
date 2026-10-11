/**
 * Student Skill Portfolio Manager - Interactive Client Scripts
 */

document.addEventListener('DOMContentLoaded', () => {
  initMobileMenu();
  initAlertDismissal();
  initSkillFilters();
  initProjectSorting();
  initLiveSearch();
  initModalBackdropClosing();
});

/* ==========================================================================
   Mobile Sidebar Toggle
   ========================================================================== */
function initMobileMenu() {
  const toggleBtn = document.querySelector('.mobile-menu-toggle');
  const sidebar = document.querySelector('.app-sidebar');

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      sidebar.classList.toggle('open');
    });

    document.addEventListener('click', (e) => {
      if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== toggleBtn) {
        sidebar.classList.remove('open');
      }
    });
  }
}

/* ==========================================================================
   Alert / Toast Auto-Dismissal
   ========================================================================== */
function initAlertDismissal() {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        alert.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(() => alert.remove(), 300);
      });
    }

    // Auto-dismiss after 6 seconds
    setTimeout(() => {
      if (alert.parentElement) {
        alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(() => alert.remove(), 400);
      }
    }, 6000);
  });
}

/* ==========================================================================
   Modal Operations (<dialog> Native API)
   ========================================================================== */
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal && typeof modal.showModal === 'function') {
    modal.showModal();
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal && typeof modal.close === 'function') {
    modal.close();
  }
}

function initModalBackdropClosing() {
  const dialogs = document.querySelectorAll('dialog.modal-dialog');
  dialogs.forEach(dialog => {
    dialog.addEventListener('click', (event) => {
      const rect = dialog.getBoundingClientRect();
      const isInDialog = (
        rect.top <= event.clientY &&
        event.clientY <= rect.top + rect.height &&
        rect.left <= event.clientX &&
        event.clientX <= rect.left + rect.width
      );
      if (!isInDialog) {
        dialog.close();
      }
    });
  });
}

/* ==========================================================================
   Dynamic Edit & Delete Modal Population
   ========================================================================== */

// Skills Edit Modal
function prepareEditSkill(id, name, category, proficiency) {
  const form = document.getElementById('editSkillForm');
  if (!form) return;

  form.action = `/skills/edit/${id}`;
  document.getElementById('edit_skill_name').value = name;
  document.getElementById('edit_skill_category').value = category;
  
  // Set proficiency radio or input
  const profSelect = document.getElementById('edit_skill_proficiency');
  if (profSelect) {
    profSelect.value = proficiency;
  }
  openModal('editSkillModal');
}

// Certificate Edit Modal
function prepareEditCertificate(id, title, issuer, issueDate, credentialId, url) {
  const form = document.getElementById('editCertForm');
  if (!form) return;

  form.action = `/certificates/edit/${id}`;
  document.getElementById('edit_cert_title').value = title;
  document.getElementById('edit_cert_issuer').value = issuer;
  document.getElementById('edit_cert_date').value = issueDate || '';
  document.getElementById('edit_cert_credential_id').value = credentialId || '';
  document.getElementById('edit_cert_url').value = url || '';
  openModal('editCertModal');
}

// Project Edit Modal
function prepareEditProject(id, title, description, technologies, duration, githubUrl, demoUrl) {
  const form = document.getElementById('editProjectForm');
  if (!form) return;

  form.action = `/projects/edit/${id}`;
  document.getElementById('edit_project_title').value = title;
  document.getElementById('edit_project_desc').value = description;
  document.getElementById('edit_project_tech').value = technologies;
  document.getElementById('edit_project_duration').value = duration || '';
  document.getElementById('edit_project_github').value = githubUrl || '';
  document.getElementById('edit_project_demo').value = demoUrl || '';
  openModal('editProjectModal');
}

// Generic Delete Confirmation Modal
function confirmDelete(type, id, displayName) {
  const modal = document.getElementById('confirmDeleteModal');
  const form = document.getElementById('deleteItemForm');
  const nameSpan = document.getElementById('deleteItemName');
  const typeSpan = document.getElementById('deleteItemType');

  if (!modal || !form) return;

  if (type === 'skill') {
    form.action = `/skills/delete/${id}`;
    if (typeSpan) typeSpan.textContent = 'skill';
  } else if (type === 'certificate') {
    form.action = `/certificates/delete/${id}`;
    if (typeSpan) typeSpan.textContent = 'certificate';
  } else if (type === 'project') {
    form.action = `/projects/delete/${id}`;
    if (typeSpan) typeSpan.textContent = 'project';
  }

  if (nameSpan) nameSpan.textContent = `"${displayName}"`;
  openModal('confirmDeleteModal');
}

/* ==========================================================================
   Skill Category Filtering
   ========================================================================== */
function initSkillFilters() {
  const filterPills = document.querySelectorAll('.skills-filter-pills .filter-pill');
  const skillCards = document.querySelectorAll('.skill-card');

  if (!filterPills.length || !skillCards.length) return;

  filterPills.forEach(pill => {
    pill.addEventListener('click', () => {
      filterPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');

      const selectedCategory = pill.getAttribute('data-category');
      const searchVal = (document.getElementById('skillSearchInput')?.value || '').toLowerCase();

      skillCards.forEach(card => {
        const cardCategory = card.getAttribute('data-category');
        const cardName = (card.getAttribute('data-name') || '').toLowerCase();

        const matchesCat = (selectedCategory === 'all' || cardCategory === selectedCategory);
        const matchesSearch = (!searchVal || cardName.includes(searchVal));

        if (matchesCat && matchesSearch) {
          card.style.display = 'flex';
        } else {
          card.style.display = 'none';
        }
      });

      checkEmptyFilterState('.cards-grid', '.skill-card', '#noSkillsFound');
    });
  });
}

/* ==========================================================================
   Live Instant Search
   ========================================================================== */
function initLiveSearch() {
  // Skills Search
  const skillSearch = document.getElementById('skillSearchInput');
  if (skillSearch) {
    skillSearch.addEventListener('input', () => {
      const query = skillSearch.value.toLowerCase().trim();
      const activePill = document.querySelector('.skills-filter-pills .filter-pill.active');
      const selectedCategory = activePill ? activePill.getAttribute('data-category') : 'all';

      document.querySelectorAll('.skill-card').forEach(card => {
        const cardName = (card.getAttribute('data-name') || '').toLowerCase();
        const cardCat = card.getAttribute('data-category') || '';
        const matchesCat = (selectedCategory === 'all' || cardCat === selectedCategory);
        const matchesSearch = (!query || cardName.includes(query) || cardCat.toLowerCase().includes(query));

        if (matchesCat && matchesSearch) {
          card.style.display = 'flex';
        } else {
          card.style.display = 'none';
        }
      });
      checkEmptyFilterState('.cards-grid', '.skill-card', '#noSkillsFound');
    });
  }

  // Certificates Search
  const certSearch = document.getElementById('certSearchInput');
  if (certSearch) {
    certSearch.addEventListener('input', () => {
      const query = certSearch.value.toLowerCase().trim();
      document.querySelectorAll('.cert-card').forEach(card => {
        const title = (card.getAttribute('data-title') || '').toLowerCase();
        const issuer = (card.getAttribute('data-issuer') || '').toLowerCase();
        const credId = (card.getAttribute('data-credential') || '').toLowerCase();

        if (!query || title.includes(query) || issuer.includes(query) || credId.includes(query)) {
          card.style.display = 'flex';
        } else {
          card.style.display = 'none';
        }
      });
      checkEmptyFilterState('.cards-grid', '.cert-card', '#noCertsFound');
    });
  }

  // Projects Search
  const projectSearch = document.getElementById('projectSearchInput');
  if (projectSearch) {
    projectSearch.addEventListener('input', () => {
      applyProjectFilters();
    });
  }
}

/* ==========================================================================
   Project Sorting & Filtering
   ========================================================================== */
function initProjectSorting() {
  const sortSelect = document.getElementById('projectSortSelect');
  if (sortSelect) {
    sortSelect.addEventListener('change', () => {
      applyProjectFilters();
    });
  }
}

function applyProjectFilters() {
  const container = document.getElementById('projectsContainer');
  const sortSelect = document.getElementById('projectSortSelect');
  const searchInput = document.getElementById('projectSearchInput');
  if (!container) return;

  const query = (searchInput?.value || '').toLowerCase().trim();
  const sortVal = sortSelect?.value || 'newest';

  const cards = Array.from(container.querySelectorAll('.project-card'));

  // Filter
  cards.forEach(card => {
    const title = (card.getAttribute('data-title') || '').toLowerCase();
    const desc = (card.getAttribute('data-desc') || '').toLowerCase();
    const tech = (card.getAttribute('data-tech') || '').toLowerCase();

    if (!query || title.includes(query) || desc.includes(query) || tech.includes(query)) {
      card.style.display = 'flex';
    } else {
      card.style.display = 'none';
    }
  });

  // Sort visible items
  cards.sort((a, b) => {
    if (sortVal === 'title-asc') {
      return a.getAttribute('data-title').localeCompare(b.getAttribute('data-title'));
    } else if (sortVal === 'title-desc') {
      return b.getAttribute('data-title').localeCompare(a.getAttribute('data-title'));
    } else if (sortVal === 'oldest') {
      return (a.getAttribute('data-date') || '').localeCompare(b.getAttribute('data-date') || '');
    } else {
      // Newest
      return (b.getAttribute('data-date') || '').localeCompare(a.getAttribute('data-date') || '');
    }
  });

  // Re-append sorted cards
  cards.forEach(card => container.appendChild(card));

  checkEmptyFilterState('#projectsContainer', '.project-card', '#noProjectsFound');
}

/* ==========================================================================
   Empty State Helper
   ========================================================================== */
function checkEmptyFilterState(containerSelector, itemSelector, emptyMsgSelector) {
  const container = document.querySelector(containerSelector);
  const emptyMsg = document.querySelector(emptyMsgSelector);
  if (!container || !emptyMsg) return;

  const items = container.querySelectorAll(itemSelector);
  let visibleCount = 0;
  items.forEach(item => {
    if (item.style.display !== 'none') {
      visibleCount++;
    }
  });

  if (visibleCount === 0 && items.length > 0) {
    emptyMsg.style.display = 'flex';
  } else {
    emptyMsg.style.display = 'none';
  }
}

/* ==========================================================================
   Clipboard Copy Helper
   ========================================================================== */
function copyToClipboard(text, btnElement) {
  if (!navigator.clipboard) return;
  navigator.clipboard.writeText(text).then(() => {
    if (btnElement) {
      const originalHtml = btnElement.innerHTML;
      btnElement.innerHTML = '<i class="fa-solid fa-check" style="color: #10b981;"></i> Copied';
      setTimeout(() => {
        btnElement.innerHTML = originalHtml;
      }, 2000);
    }
  });
}
