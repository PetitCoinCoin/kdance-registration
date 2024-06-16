$(document).ready(() => {
  populateWeekdays();
  getSeasons();
  postSeason();
  getTeachers();
  postTeacher();
  patchTeacher();
  deleteTeacher();
  createUpdateCourse();
  seasonSelect = document.querySelector('#season-select');
  seasonSelect.addEventListener('change', () => 
    onSeasonChange(seasonSelect.val(), seasonSelect[0].options[seasonSelect[0].selectedIndex].innerHTML)
  );
});

function populateWeekdays() {
  weekdaySelectAdd = $('#course-weekday');
  for (let key in WEEKDAY) {
    weekdaySelectAdd.append($('<option>', { value: key, text: WEEKDAY[key] }));
  }
}

function getSeasons() {
  $.ajax({
    url: seasonsUrl,
    type: 'GET',
    success: (data) => {
      seasonSelect = $('#season-select');
      data.map((season) => {
        let label = season.year;
        if (season.is_current) {
          // TODO: modifier pour que ce soit au moment où on ouvre la modale (pour changer si edit)
          label += ' (en cours)'
          $('#course-modal-title').html(`Ajouter un cours pour la saison ${season.year}`);
          $('#course-season').val(season.id);
          getCourses(season.id);
        }
        seasonSelect.append($('<option>', { value: season.id, text: label, selected: season.is_current }));
      });
    },
    error: (error) => {
      // if (!error.responseJSON) {
      //     $('#message-error-signup').removeAttr('hidden');
      // }
    }
  });
}

function postSeason() {
  $('#form-add-season').submit((event) => {
    $('.invalid-feedback').removeClass('d-inline');
    event.preventDefault();
    const data = {
      year: $('#year-add').val(),
      is_current: $('#current-add').is(':checked'),
    };
    $.ajax({
      url: seasonsUrl,
      type: 'POST',
      contentType: 'application/json',
      headers: { 'X-CSRFToken': csrftoken },
      mode: 'same-origin',
      data: JSON.stringify(data),
      dataType: 'json',
      success: () => {
        event.currentTarget.submit();
      },
      error: (error) => {
        // if (!error.responseJSON) {
        //   $('#message-error-signup').removeAttr('hidden');
        // }
        if (error.responseJSON.year) {
          $('#invalid-year-add').html(error.responseJSON.year[0]);
          $('#invalid-year-add').addClass('d-inline');
        }
      }
    });
  });
}

function onSeasonChange(seasonId, seasonYear) {
  // $('#course-modal-title').html(`Ajouter un cours pour la saison ${seasonYear}`);
  // $('#course-season').val(seasonId);
  getCourses(seasonId);
}

function getCourses(seasonId) {
  $.ajax({
    url: coursesUrl + `?season=${seasonId}`,
    type: 'GET',
    success: (data) => {
      $('#courses-list').empty()
      const listParent = document.querySelector('#courses-list');
      const courseTemplate = document.querySelector('#course-item-template');
      data.map((course) => {
        const clone = courseTemplate.content.cloneNode(true);
        let td = clone.querySelectorAll('td');
        const startHour = course.start_hour.split(':');
        const endHour = course.end_hour.split(':');
        td[0].innerHTML = course.name;
        td[1].innerHTML = course.teacher.name;
        td[2].innerHTML = `${WEEKDAY[course.weekday]}, ${startHour[0]}h${startHour[1]}-${endHour[0]}h${endHour[1]}`;
        td[3].innerHTML = course.price + '€';
        let buttons = clone.querySelectorAll('button');        
        buttons[0].id = `edit-course-${course.id}-btn`;
        buttons[0].dataset.bsCid = course.id;
        buttons[1].id = `delete-course-${course.id}-btn`;
        buttons[1].dataset.bsCid = course.id;
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

function getTeachers() {
  $.ajax({
    url: teachersUrl,
    type: 'GET',
    success: (data) => {
      const listParent = document.querySelector('#teachers-list');
      const teacherTemplate = document.querySelector('#teacher-item-template');
      teacherSelect = $('#course-teacher');
      data.map((teacher) => {
        teacherSelect.append($('<option>', { value: teacher.id, text: teacher.name }));
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

function postTeacher() {
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
    });
  });
}

function patchTeacher() {
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
        patchTeacherRequest(teacherId, event);
      });
    })
  }
}

function patchTeacherRequest(teacher, event) {
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

function createUpdateCourse() {
  const courseModal = document.getElementById('course-modal');
  if (courseModal) {
    courseModal.addEventListener('show.bs.modal', event => {
      const button = event.relatedTarget;
      const course = button.getAttribute('data-bs-cid');
      if (course !== null) {
        getCourse(course);
        $('#course-btn').html('Modifier');
        patchCourse(course);
      } else {
        $('#course-btn').html('Ajouter');
        postCourse();
      }
    });
  }
}

function getCourse(course) {
  $.ajax({
    url: coursesUrl + course + '/',
    type: 'GET',
    success: (data) => {
      seasonYear = seasonSelect[0].options[seasonSelect[0].selectedIndex].innerHTML
      $('#course-modal-title').html(`Modifier le cours '${data.name}' pour la saison ${seasonYear}`);
      $('#course-name').val(data.name);
      $('#course-teacher').val(data.teacher.id);
      $('#course-price').val(data.price);
      $('#course-weekday').val(data.weekday);
      $('#course-start').val(data.start_hour.substring(0, 5));
      $('#course-end').val(data.end_hour.substring(0, 5));
    },
    error: (error) => {
      // if (!error.responseJSON) {
      //     $('#message-error-signup').removeAttr('hidden');
      // }
    }
  });
}

function getCourseData() {
  return {
    name: $('#course-name').val(),
    teacher: $('#course-teacher').val(),
    season: seasonSelect.val(),
    price: $('#course-price').val(),
    weekday: $('#course-weekday').val(),
    start_hour: $('#course-start').val(),
    end_hour: $('#course-end').val(),
  }
}

function postCourse() {
  seasonYear = seasonSelect[0].options[seasonSelect[0].selectedIndex].innerHTML
  $('#course-modal-title').html(`Ajouter un cours pour la saison ${seasonYear}`);
  $('#form-course').submit((event) => {
    $('.invalid-feedback').removeClass('d-inline');
    event.preventDefault();
    $.ajax({
      url: coursesUrl,
      type: 'POST',
      contentType: 'application/json',
      headers: { 'X-CSRFToken': csrftoken },
      mode: 'same-origin',
      data: JSON.stringify(getCourseData()),
      dataType: 'json',
      success: () => {
        event.currentTarget.submit();
      },
      error: (error) => {
        // if (!error.responseJSON) {
        //   $('#message-error-signup').removeAttr('hidden');
        // }
      }
    });
  });
}

function patchCourse(course) {
  $('#form-course').submit((event) => {
    $('.invalid-feedback').removeClass('d-inline');
    event.preventDefault();
    $.ajax({
      url: coursesUrl + course + '/',
      type: 'PATCH',
      contentType: 'application/json',
      headers: { 'X-CSRFToken': csrftoken },
      mode: 'same-origin',
      data: JSON.stringify(getCourseData()),
      dataType: 'json',
      success: () => {
        event.currentTarget.submit();
      },
      error: (error) => {
        // if (!error.responseJSON) {
        //   $('#message-error-signup').removeAttr('hidden');
        // }
      }
    });
  }); 
}
