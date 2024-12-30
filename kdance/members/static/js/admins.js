$(document).ready(() => {
  displayToast();
  handleEmails();
  getUsersAdmins();
  getUsersTeachers();
  updateUserAdmin();
  breadcrumbDropdownOnHover();
});

function displayToast() {
  var urlParams = new URLSearchParams(window.location.search);
  let unprocessed = [];
  if (urlParams.get('not_found') !== null) {
    unprocessed.push(`Les adresses suivantes n'ont pas été trouvées dans la base: ${urlParams.get('not_found')}`);
  }
  if (urlParams.get('other') !== null) {
    unprocessed.push(`Une erreur est survenue avec ces adresses: ${urlParams.get('other')}. Ré-essayez plus tard ou contactez le support.`);
  }
  if (unprocessed.length > 0) {
    const toast = bootstrap.Toast.getOrCreateInstance(document.getElementById('admin-warning-toast'));
    $('#admin-warning-body').text(unprocessed.join('\n'))
    toast.show();
  }

}

function handleEmails() {
  const emailParent = document.querySelector('#emails-div');
  const emailTemplate = document.querySelector('#email-template');
  $('#emails-div').on('click', '.add-email-btn', () => {
    emailParent.appendChild(emailTemplate.content.cloneNode(true));
  });
  $('#emails-div').on('click', '.remove-email-btn', (event) => {
    const parentDiv = event.currentTarget.parentElement.parentElement;
    parentDiv.remove();
  });
}

function actionAdminFormatter(value, row) {
  return `<button class="btn btn-outline-warning btn-sm" item="admin" userEmail="${row.email}" userName="${row.first_name} ${row.last_name}" type="button" data-bs-toggle="modal" data-bs-target="#confirm-deactivate-modal"><i class="bi-person-fill-lock"></i></button>`;
}

function actionTeacherFormatter(value, row) {
  return `<button class="btn btn-outline-warning btn-sm" item="teacher" userEmail="${row.email}" userName="${row.first_name} ${row.last_name}" type="button" data-bs-toggle="modal" data-bs-target="#confirm-deactivate-modal"><i class="bi-person-fill-lock"></i></button>`;
}

function getUsersAdmins() {
  $('#message-error-admin').addClass('d-none');
  $.ajax({
    url: usersUrl + '?admin=true',
    type: 'GET',
    success: (data) => {
      // Bootstrap table not initialised
      if (document.querySelector('#admins-table').className === '') {
        $('#admins-table').bootstrapTable({
          locale: 'fr-FR',
          columns: [{
            field: 'last_name',
            title: 'Nom de famille',
            searchable: true,
            sortable: true,
          }, {
            field: 'first_name',
            title: 'Prénom',
            searchable: true,
            sortable: true,
          }, {
            field: 'email',
            title: 'Email',
            searchable: true,
            sortable: false,
          }, {
            field: 'profile.phone',
            title: 'Téléphone',
            searchable: false,
            sortable: false,
          }, {
            field: 'operate',
            title: 'Retirer des admins',
            align: 'center',
            clickToSelect: false,
            formatter: actionAdminFormatter,
          }],
          data: data
        });
        $('input[type=search]').attr('placeholder', 'Rechercher');
        // Already initialised
      } else {
        $('#admins-table').bootstrapTable('load', data);
      }
    },
    error: (error) => {
      if (!error.responseJSON) {
        $('#message-error-modal').text(DEFAULT_ERROR_MESSAGE);
        $('#message-error-admin').removeClass('d-none');
      }
    }
  });
}

function getUsersTeachers() {
  $('#message-error-admin-teacher').addClass('d-none');
  $.ajax({
    url: usersUrl + '?teacher=true',
    type: 'GET',
    success: (data) => {
      // Bootstrap table not initialised
      if (document.querySelector('#teachers-table').className === '') {
        $('#teachers-table').bootstrapTable({
          locale: 'fr-FR',
          columns: [{
            field: 'last_name',
            title: 'Nom de famille',
            searchable: true,
            sortable: true,
          }, {
            field: 'first_name',
            title: 'Prénom',
            searchable: true,
            sortable: true,
          }, {
            field: 'email',
            title: 'Email',
            searchable: true,
            sortable: false,
          }, {
            field: 'profile.phone',
            title: 'Téléphone',
            searchable: false,
            sortable: false,
          }, {
            field: 'operate',
            title: 'Retirer les droits du professeur',
            align: 'center',
            clickToSelect: false,
            formatter: actionTeacherFormatter,
          }],
          data: data
        });
        $('input[type=search]').attr('placeholder', 'Rechercher');
        // Already initialised
      } else {
        $('#teachers-table').bootstrapTable('load', data);
      }
    },
    error: (error) => {
      if (!error.responseJSON) {
        $('#message-error-modal').text(DEFAULT_ERROR_MESSAGE);
        $('#message-error-admin-teacher').removeClass('d-none');
      }
    }
  });
}

function updateUserAdmin() {
  const adminModal = document.getElementById('admin-modal');
  const deleteModal = document.getElementById('confirm-deactivate-modal');
  if (adminModal) {
    adminModal.addEventListener('show.bs.modal', event => {
      $('#message-error-modal').addClass('d-none');
      const button = event.relatedTarget;
      if (button.getAttribute('id') === 'add-admin-btn') {
        $('.modal-title').html('Ajouter des nouveaux admins');
        $('#form-admin').data('item', 'admin');
      } else {
        $('.modal-title').html('Ajouter des droits à un professeur');
        $('#form-admin').data('item', 'teacher');
      }
    });
    $('#admin-modal').on('submit', '#form-admin', function(event) {
      event.preventDefault();
      const action = 'activate';
      const item = $(this).data('item');
      const data = Object.values($('#admin-modal input')).map(i => i.value).filter(e => e !== undefined && e !== "");
      putUser(item, action, data);
    })
  }
  if (deleteModal) {
    deleteModal.addEventListener('show.bs.modal', event => {
      const button = event.relatedTarget;
      const email = button.getAttribute('userEmail');
      const name = button.getAttribute('userName');
      const modalBody = deleteModal.querySelector('.modal-body');
      const item = button.getAttribute('item');
      if (item === 'admin') {
        $('.modal-title').html('Supprimer un admin');
        modalBody.textContent = `Etes-vous sur.e de vouloir supprimer ${name} de la liste des admins ?`;
      } else {
        $('.modal-title').html('Retirer les droits d\'un professeur');
        modalBody.textContent = `Etes-vous sur.e de vouloir retirer les droits de ${name} en tant que professeur ?`;
      }
      $(document).on('click', '#delete-admin-btn', function(){
        const action = 'deactivate';
        const data = [email];
        putUser(item, action, data);
      });
    });
  }
}

function putUser(item, action, data) {
    $('#message-error-admin').addClass('d-none');
    $('#message-error-admin-teacher').addClass('d-none');
    $('.invalid-feedback').removeClass('d-inline');
    const url = item === 'admin' ? usersAdminActionUrl : usersTeacherActionUrl;
    $.ajax({
      url: url + action + '/',
      type: 'PUT',
      contentType: 'application/json',
      headers: { 'X-CSRFToken': csrftoken },
      mode: 'same-origin',
      data: JSON.stringify({emails: data}),
      dataType: 'json',
      success: (resp) => {
        let unprocessed = {};
        if (resp.not_found.length > 0) {
          unprocessed.not_found = resp.not_found;
        }
        if (resp.other.length > 0) {
          unprocessed.other = resp.other;
        }
        window.location.href = window.location.pathname + '?' + new URLSearchParams(unprocessed).toString();
      },
      error: (error) => {
        $('#message-error-modal').removeClass('d-none');
        if (!error.responseJSON) {
          $('#message-error-modal').text(DEFAULT_ERROR_MESSAGE);
        }
        if (error.responseJSON && error.responseJSON.not_found) {
          $('#message-error-modal').text(`Les adresses suivantes n'ont pas été trouvées dans la base: ${error.responseJSON.not_found.join(', ')}`);
        } else if (error.responseJSON && error.responseJSON.other) {
          $('#message-error-modal').text(`Une erreur est survenue avec ces adresses: ${error.responseJSON.not_found.join(', ')}. Ré-essayez plus tard ou contactez le support.`);
        }
        if (error.responseJSON && error.responseJSON.emails) {
          const toast = bootstrap.Toast.getOrCreateInstance(document.getElementById('admin-warning-toast'));
          $('#admin-warning-body').text(error.responseJSON.emails[0])
          toast.show();
        }
      }
    });
}
