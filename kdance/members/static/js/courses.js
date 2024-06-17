$(document).ready(() => {
  populateWeekdays();
  getSeasons();
  getTeachers();
  createUpdateSeason();
  createUpdateTeacher();
  createUpdateCourse();
  deleteItem();
  seasonSelect = document.querySelector('#season-select');
  seasonSelect.addEventListener('change', () => 
    onSeasonChange(seasonSelect.val())
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
          label += ' (en cours)'
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

function getSeason(season) {
  $.ajax({
    url: seasonsUrl + season,
    type: 'GET',
    success: (data) => {
      $('#season-year').val(data.year);
      $('#season-current').prop('checked', data.is_current);
    },
    error: (error) => {
      // if (!error.responseJSON) {
      //     $('#message-error-signup').removeAttr('hidden');
      // }
    }
  });
}

function createUpdateSeason() {
  const seasonModal = document.getElementById('season-modal');
  if (seasonModal) {
    seasonModal.addEventListener('show.bs.modal', event => {
      const button = event.relatedTarget;
      let url = seasonsUrl;
      let method = 'POST';
      if (button.getAttribute('id') === 'add-season-btn') {
        $('#season-modal-title').html('Ajouter une nouvelle saison');
        $('#season-btn').html('Ajouter');
      } else {
        $('#season-modal-title').html('Modifier une saison');
        $('#season-btn').html('Modifier');
        getSeason(seasonSelect.val());
        url = url + seasonSelect.val() + '/';
        method = 'PATCH';
      }
      postOrPatchSeason(url, method);
    });
  }
}

function postOrPatchSeason(url, method) {
  $('#form-season').submit((event) => {
    $('.invalid-feedback').removeClass('d-inline');
    event.preventDefault();
    const data = {
      year: $('#season-year').val(),
      is_current: $('#season-current').is(':checked'),
    };
    $.ajax({
      url: url,
      type: method,
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
          $('#invalid-season-year').html(error.responseJSON.year[0]);
          $('#invalid-season-year').addClass('d-inline');
        }
      }
    });
  });
}

function onSeasonChange(seasonId) {
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
        buttons[0].dataset.bsTname = teacher.name;
        buttons[0].dataset.bsTid = teacher.id;
        buttons[1].id = `delete-${teacher.id}-btn`;
        buttons[1].dataset.bsTname = teacher.name;
        buttons[1].dataset.bsTid = teacher.id;
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

function createUpdateTeacher() {
  const teacherModal = document.getElementById('teacher-modal');
  if (teacherModal) {
    teacherModal.addEventListener('show.bs.modal', event => {
      const button = event.relatedTarget;
      const teacher = button.getAttribute('data-bs-Tid');
      const teacherName = button.getAttribute('data-bs-Tname');
      if (teacher !== null) {
        $('#teacher-modal-title').html('Modifier un professeur');
        $('#teacher-btn').html('Modifier');
        $('#teacher-name').val(teacherName);
      } else {
        $('#teacher-modal-title').html('Ajouter un professeur');
        $('#teacher-btn').html('Ajouter');
      }
      postOrPatchTeacher(teacher);
    });
  }
}

function postOrPatchTeacher(teacher) {
  const method = teacher === null ? 'POST' : 'PATCH';
  const url = teacher === null ? teachersUrl : teachersUrl + teacher + '/';
  $('#form-teacher').submit((event) => {
    $('.invalid-feedback').removeClass('d-inline');
    event.preventDefault();
    $.ajax({
      url: url,
      type: method,
      contentType: 'application/json',
      headers: { 'X-CSRFToken': csrftoken },
      mode: 'same-origin',
      data: JSON.stringify({ name: $('#teacher-name').val() }),
      dataType: 'json',
      success: () => {
        event.currentTarget.submit();
      },
      error: (error) => {
        // if (!error.responseJSON) {
        //   $('#message-error-signup').removeAttr('hidden');
        // }
        if (error.responseJSON.name) {
          $('#invalid-teacher-name').html(error.responseJSON.name[0]);
          $('#invalid-teacher-name').addClass('d-inline');
        }
      }
    });
  });
}

function createUpdateCourse() {
  const courseModal = document.getElementById('course-modal');
  if (courseModal) {
    courseModal.addEventListener('show.bs.modal', event => {
      const button = event.relatedTarget;
      const course = button.getAttribute('data-bs-cid');
      if (course !== null) {
        getCourse(course, null);
        $('#course-btn').html('Modifier');
      } else {
        const seasonYear = seasonSelect[0].options[seasonSelect[0].selectedIndex].innerHTML
        $('#course-modal-title').html(`Ajouter un cours pour la saison ${seasonYear}`);
        $('#course-btn').html('Ajouter');
      }
      postOrPatchCourse(course);
    });
  }
}

function getCourse(course, deleteModalBody) {
  $.ajax({
    url: coursesUrl + course + '/',
    type: 'GET',
    success: (data) => {
      const seasonYear = seasonSelect[0].options[seasonSelect[0].selectedIndex].innerHTML
      $('#course-modal-title').html(`Modifier le cours '${data.name}' pour la saison ${seasonYear}`);
      if (deleteModalBody !== null) {
        deleteModalBody.textContent = `Etes-vous sur.e de vouloir supprimer le cours '${data.name}' pour la saison ${seasonYear} ?`;
      }
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

function postOrPatchCourse(course) {
  const method = course === null ? 'POST' : 'PATCH';
  const url = course === null ? coursesUrl : coursesUrl + course + '/';
  $('#form-course').submit((event) => {
    $('.invalid-feedback').removeClass('d-inline');
    event.preventDefault();
    const data = {
      name: $('#course-name').val(),
      teacher: $('#course-teacher').val(),
      season: seasonSelect.val(),
      price: $('#course-price').val(),
      weekday: $('#course-weekday').val(),
      start_hour: $('#course-start').val(),
      end_hour: $('#course-end').val(),
    }
    $.ajax({
      url: url,
      type: method,
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
      }
    });
  });
}

function deleteItem() {
  const deleteModal = document.getElementById('delete-modal');
  if (deleteModal) {
    deleteModal.addEventListener('show.bs.modal', event => {
      const button = event.relatedTarget;
      const teacher = button.getAttribute('data-bs-tname');
      const teacherId = button.getAttribute('data-bs-tid');
      const courseId = button.getAttribute('data-bs-cid');
      const modalBody = deleteModal.querySelector('.modal-body');
      let url = '';
      if (teacherId !== null) {
        // Teacher deletion
        $('#delete-modal-title').html('Supprimer un professeur');
        modalBody.textContent = `Etes-vous sur.e de vouloir supprimer ${teacher} de la liste des professeurs ?`;
        url =  teachersUrl + teacherId + '/ ';
      } else if (courseId !== null) {
        // Course deletion
        $('#delete-modal-title').html('Supprimer un cours');
        getCourse(courseId, modalBody);
        url = coursesUrl + courseId + '/';
      } else {
        // Season deletion
        $('#delete-modal-title').html('Supprimer une saison');
        const seasonYear = seasonSelect[0].options[seasonSelect[0].selectedIndex].innerHTML;
        modalBody.textContent = `Etes-vous sur.e de vouloir supprimer la saison ${seasonYear} ainsi que ses cours associés ?`;
        url = seasonsUrl + seasonSelect.val() + '/';
      }
      $(document).on("click", "#delete-btn", function(){
        $.ajax({
          url: url,
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
      });
    });
  }
}
