$(document).ready(() => {
  getSeasons();
  getTeachers();
  postTeachers();
  putTeacher();
  deleteTeacher();
});

function getSeasons() {
  $.ajax({
    url: seasonsUrl,
    type: 'GET',
    success: (data) => {
      seasonSelect = $('#season-select');
      data.map((season) => {
        let label = season.year;
        if (season.is_current) {
          label += ' (en cours)'
        }
        seasonSelect.append($('<option>', { value: season.year, text: label, selected: season.is_current }));
      });
    },
    error: (error) => {
      // if (!error.responseJSON) {
      //     $('#message-error-signup').removeAttr('hidden');
      // }
    }
  });
}

function getTeachers() {
  $.ajax({
    url: teachersUrl,
    type: 'GET',
    success: (data) => {
      const listParent = document.querySelector('#teachers-list');
      const teacherTemplate = document.querySelector('#teacher-item-template');
      data.map((teacher) => {
        const clone = teacherTemplate.content.cloneNode(true);
        let name = clone.querySelector('span');
        name.textContent = teacher.name;
        let avatar = clone.querySelector('img');
        avatar.src = `https://api.dicebear.com/8.x/thumbs/svg?seed=${teacher.name}&radius=50`;
        let buttons = clone.querySelectorAll('button');
        buttons[0].id = `edit-${teacher.id}-btn`;
        buttons[0].dataset.bsTname = `${teacher.name}`;
        buttons[0].dataset.bsTid = `${teacher.id}`;
        buttons[1].id = `delete-${teacher.id}-btn`;
        buttons[1].dataset.bsTname = `${teacher.name}`;
        buttons[1].dataset.bsTid = `${teacher.id}`;
        listParent.appendChild(clone);
      });
    },
    error: (error) => {
      // if (!error.responseJSON) {
      //     $('#message-error-signup').removeAttr('hidden');
      // }
    }
  });
}

function postTeachers() {
  $('#form-add-teacher').submit((event) => {
    $('.invalid-feedback').removeClass('d-inline');
    event.preventDefault();
    $.ajax({
      url: teachersUrl,
      type: 'POST',
      contentType: 'application/json',
      headers: { 'X-CSRFToken': csrftoken },
      mode: 'same-origin',
      data: JSON.stringify({ name: $('#name-add').val() }),
      dataType: 'json',
      success: () => {
        event.currentTarget.submit();
      },
      error: (error) => {
        // if (!error.responseJSON) {
        //   $('#message-error-signup').removeAttr('hidden');
        // }
        if (error.responseJSON.name) {
          $('#invalid-name-add').html(error.responseJSON.name[0]);
          $('#invalid-name-add').addClass('d-inline');
        }
      }
    }); $
  });
}

function putTeacher() {
  const editTeacherModal = document.getElementById('edit-teacher-modal');
  if (editTeacherModal) {
    editTeacherModal.addEventListener('show.bs.modal', event => {
      const button = event.relatedTarget;
      const teacher = button.getAttribute('data-bs-tname');
      const teacherId = button.getAttribute('data-bs-tid');
      const modalBodyInput = editTeacherModal.querySelector('.modal-body input');
      modalBodyInput.value = teacher;
      $('#form-edit-teacher').submit((event) => {
        $('.invalid-feedback').removeClass('d-inline');
        event.preventDefault();
        putTeacherRequest(teacherId, event);
      });
    })
  }
}

function putTeacherRequest(teacher, event) {
  $.ajax({
    url: teachersUrl + teacher + '/',
    type: 'PATCH',
    contentType: 'application/json',
    headers: { 'X-CSRFToken': csrftoken },
    mode: 'same-origin',
    data: JSON.stringify({ name: $('#name-edit').val() }),
    dataType: 'json',
    success: () => {
      event.currentTarget.submit();
    },
    error: (error) => {
      // if (!error.responseJSON) {
      //   $('#message-error-signup').removeAttr('hidden');
      // }
      if (error.responseJSON.name) {
        $('#invalid-name-edit').html(error.responseJSON.name[0]);
        $('#invalid-name-edit').addClass('d-inline');
      }
    }
  }); 
}

function deleteTeacher() {
  const deleteTeacherModal = document.getElementById('delete-teacher-modal');
  if (deleteTeacherModal) {
    deleteTeacherModal.addEventListener('show.bs.modal', event => {
      const button = event.relatedTarget;
      const teacher = button.getAttribute('data-bs-tname');
      const teacherId = button.getAttribute('data-bs-tId');
      const modalBody = deleteTeacherModal.querySelector('.modal-body');
      modalBody.textContent = `Etes-vous sur.e de vouloir supprimer ${teacher} de la liste des professeurs ?`;
      $(document).on("click", "#delete-teacher-btn", function(){
        deleteTeacherRequest(teacherId);
      });
    });
  }
}

function deleteTeacherRequest(teacher) {
  $.ajax({
    url: teachersUrl + teacher,
    type: 'DELETE',
    headers: { 'X-CSRFToken': csrftoken },
    mode: 'same-origin',
    success: () => {
      location.reload();
    },
    error: (error) => {
      // if (!error.responseJSON) {
      //   $('#message-error-signup').removeAttr('hidden');
      // }
    }
  });
}