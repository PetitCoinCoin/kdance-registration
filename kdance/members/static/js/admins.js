$(document).ready(() => {
  handleEmails();
  getUsersAdmins();
  updateUserAdmin();
});

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

function getUsersAdmins() {
  $.ajax({
    url: usersUrl + '?admin=true',
    type: 'GET',
    success: (data) => {
      // Bootstrap table not initialised
      if (document.querySelector('#admins-table').className === '') {
        $('#admins-table').bootstrapTable({
          search: true,
          stickyHeader: true,
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
            formatter: function (value, row, index) {
              return `<button class="btn btn-outline-warning btn-sm" userEmail="${row.email}" userName="${row.first_name} ${row.last_name}" type="button" data-bs-toggle="modal" data-bs-target="#confirm-deactivate-modal"><i class="bi-person-fill-lock"></i></button>`;
            }
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
      // if (!error.responseJSON) {
      //     $('#message-error-signup').removeAttr('hidden');
      // }
    }
  });
}

function updateUserAdmin() {
  const adminModal = document.getElementById('admin-modal');
  const deleteModal = document.getElementById('confirm-deactivate-modal');
  if (adminModal) {
    $('#admin-modal').on('submit', '#form-admin', function(event) {
      event.preventDefault();
      const action = 'activate';
      const data = Object.values($('#admin-modal input')).map(i => i.value).filter(e => e !== undefined && e !== "");
      putUser(action, data, event);
    })
  }
  if (deleteModal) {
    deleteModal.addEventListener('show.bs.modal', event => {
      const button = event.relatedTarget;
      const email = button.getAttribute('userEmail');
      const name = button.getAttribute('userName');
      const modalBody = deleteModal.querySelector('.modal-body');
      $('#delete-modal-title').html('Supprimer un professeur');
      modalBody.textContent = `Etes-vous sur.e de vouloir supprimer ${name} de la liste des admins ?`;
      $(document).on('click', '#delete-admin-btn', function(){
        const action = 'deactivate';
        const data = [email];
        putUser(action, data, null);
      });
    });
  }
}

function putUser(action, data, event) {
    $('.invalid-feedback').removeClass('d-inline');
    $.ajax({
      url: usersAdminActionUrl + action + '/',
      type: 'PUT',
      contentType: 'application/json',
      headers: { 'X-CSRFToken': csrftoken },
      mode: 'same-origin',
      data: JSON.stringify({emails: data}),
      dataType: 'json',
      success: () => {
        event?.currentTarget !== null ? event.currentTarget.submit() : location.reload();
      },
      error: (error) => {
        // if (!error.responseJSON) {
        //   $('#message-error-signup').removeAttr('hidden');
        // }
      }
    });
  // });
}
