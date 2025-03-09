$(document).ready(() => {
  populateWeekdays();
  getSeasons();
  getTeachers();
  createUpdateSeason();
  createUpdateTeacher();
  createUpdateCourse();
  copyCourseFromSeason();
  deleteItem();
  const seasonSelect = document.querySelector('#season-select');
  seasonSelect.addEventListener('change', () =>
    onSeasonChange(seasonSelect.value)
  );
  breadcrumbDropdownOnHover();
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
      data.map((season) => {
        let label = season.year;
        if (season.is_current) {
          label += ' (en cours)';
          getCourses(season.id);
          $('#copy-modal-title').html(`Ajouter des cours à la saison ${season.year}`);
        } else {
          $('#copy-season').append($('<option>', { value: season.id, text: season.year }));
        }
        $('#season-select').append($('<option>', { value: season.id, text: label, selected: season.is_current }));
      });
    },
    error: (error) => {
      showToast('Impossible de récupérer la liste des saisons.');
      console.log(error);
    }
  });
}

function getSeason(season) {
  $('.invalid-feedback').removeClass('d-inline');
  $.ajax({
    url: seasonsUrl + season,
    type: 'GET',
    success: (data) => {
      $('#season-year').val(data.year);
      $('#season-current').prop('checked', data.is_current);
      $('#season-discount-percent').val(data.discount_percent);
      $('#season-discount-limit').val(data.discount_limit);
      $('#season-pass-sport-amount').val(data.pass_sport_amount);
    },
    error: (error) => {
      showToast('Impossible de récupérer les informations de la saison.');
      console.log(error);
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
      $('.invalid-feedback').removeClass('d-inline');
      if (button.getAttribute('id') === 'add-season-btn') {
        document.getElementById('form-season').reset();
        $('#season-modal-title').html('Ajouter une nouvelle saison');
        $('#season-btn').html('Ajouter');
      } else {
        $('#season-modal-title').html('Modifier une saison');
        $('#season-btn').html('Modifier');
        getSeason($('#season-select').val());
        url = url + $('#season-select').val() + '/';
        method = 'PATCH';
      }
      postOrPatchSeason(url, method);
    });
  }
}

function postOrPatchSeason(url, method) {
  $('#form-season').submit((event) => {
    event.preventDefault();
    const data = {
      year: $('#season-year').val(),
      is_current: $('#season-current').is(':checked'),
    };
    if ($('#season-discount-percent').val() !== '') {
      data['discount_percent'] = $('#season-discount-percent').val();
    }
    if ($('#season-discount-limit').val() !== '') {
      data['discount_limit'] = $('#season-discount-limit').val();
    }
    if ($('#season-pass-sport-amount').val() !== '') {
      data['pass_sport_amount'] = $('#season-pass-sport-amount').val();
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
        if (!error.responseJSON) {
          showToast(DEFAULT_ERROR);
          console.log(error);
        }
        if (error.responseJSON.year) {
          $('#invalid-season-year').html(error.responseJSON.year[0] + ' Format attendu: XXXX-YYYY');
          $('#invalid-season-year').addClass('d-inline');
        }
      }
    });
  });
}

function copyCourseFromSeason() {
  $('#form-copy').submit((event) => {
    $('.invalid-feedback').removeClass('d-inline');
    event.preventDefault();
    $.ajax({
      url: copyCoursesUrl,
      type: 'POST',
      contentType: 'application/json',
      headers: { 'X-CSRFToken': csrftoken },
      mode: 'same-origin',
      data: JSON.stringify({
        from_season: parseInt($('#copy-season').val(), 10),
        to_season: parseInt($('#season-select').val(), 10),
      }),
      dataType: 'json',
      success: (data) => {
        event.currentTarget.submit();
      },
      error: (error) => {
        showToast(DEFAULT_ERROR);
        console.log(error);
      }
    });
  });
}

function onSeasonChange(seasonId) {
  getCourses(seasonId);
  getPreviousSeason(seasonId);
  const seasonSelect = $('#season-select');
  const seasonYear = seasonSelect[0].options[seasonSelect[0].selectedIndex].innerHTML;
  if (!seasonYear.includes('en cours') || $('#copy-season')[0].options.length === 0) {
    $('#copy-courses-btn').addClass('d-none');
  } else {
    $('#copy-courses-btn').removeClass('d-none');
  }
}

function getPreviousSeason(seasonId) {
  const seasonSelect = $('#season-select');
  const seasonYear = seasonSelect[0].options[seasonSelect[0].selectedIndex].innerHTML
  $('#copy-modal-title').html(`Ajouter des cours à la saison ${seasonYear}`);
  let copySelect = $('#copy-season');
  copySelect.empty();
  for (var i = 0; i < seasonSelect[0].options.length; i++) {
    option = seasonSelect[0].options[i]
    if (option.value !== seasonId) {
      copySelect.append($('<option>', { value: option.value, text: option.innerHTML }));
    }
  }
}

function actionFormatter(value, row) {
  return `<button id="edit-course-${row.id}-btn" class="btn btn-outline-info btn-sm" type="button" data-bs-cid=${row.id} data-bs-toggle="modal" data-bs-target="#course-modal">
            <i class="bi-pencil-fill"></i>
          </button>
          <button id="delete-course-${row.id}-btn" class="btn btn-outline-danger btn-sm" type="button" data-bs-cid=${row.id} data-bs-toggle="modal" data-bs-target="#delete-modal">
            <i class="bi-trash3-fill"></i>
          </button>`;
}

function getCourses(seasonId) {
  $.ajax({
    url: coursesUrl + `?season=${seasonId}`,
    type: 'GET',
    success: (data) => {
      // Bootstrap table not initialised
      if (document.querySelector('#courses-table').className === '') {
        $('#courses-table').bootstrapTable({
          ...COMMON_TABLE_PARAMS,
          showFullscreen: false,
          showColumns: false,
          columns: [{
            field: 'name',
            title: 'Nom',
            searchable: true,
            sortable: true,
          }, {
            field: 'teacher.name',
            title: 'Professeur',
            searchable: true,
            sortable: true,
          }, {
            field: 'slot',
            title: 'Créneau',
            searchable: true,
            sortable: true,
          }, {
            field: 'price',
            title: 'Tarif',
            searchable: false,
            sortable: false,
          }, {
            field: 'operate',
            title: 'Actions',
            align: 'center',
            clickToSelect: false,
            formatter: actionFormatter,
          }],
          data: data.map(c => {
            const startHour = c.start_hour.split(':');
            const endHour = c.end_hour.split(':');
            return {
              ...c,
              price: c.price + '€',
              slot: `${WEEKDAY[c.weekday]}, ${startHour[0]}h${startHour[1]}-${endHour[0]}h${endHour[1]}`
            }
          })
        });
        $('input[type=search]').attr('placeholder', 'Rechercher');
        // Already initialised
      } else {
        $('#courses-table').bootstrapTable('load', data.map(c => {
          const startHour = c.start_hour.split(':');
          const endHour = c.end_hour.split(':');
          return {
            ...c,
            price: c.price + '€',
            slot: `${WEEKDAY[c.weekday]}, ${startHour[0]}h${startHour[1]}-${endHour[0]}h${endHour[1]}`
          }
        }));
      }
    },
    error: (error) => {
      showToast('Impossible de récupérer les cours de la saison.');
      console.log(error);
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
      showToast('Impossible de récupérer la liste des professeurs.');
      console.log(error);
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
        if (!error.responseJSON) {
          showToast(DEFAULT_ERROR);
          console.log(error);
        }
        if (error.responseJSON && error.responseJSON.name) {
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
        document.getElementById('form-course').reset();
        const seasonSelect = $('#season-select');
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
      const seasonSelect = $('#season-select');
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
      showToast('Impossible de récupérer les informations du cours.');
      console.log(error);
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
      season: $('#season-select').val(),
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
        if (!error.responseJSON) {
          showToast(DEFAULT_ERROR);
          console.log(error);
        }
        if (error.responseJSON && error.responseJSON.non_field_errors) {
          const toast = bootstrap.Toast.getOrCreateInstance(document.getElementById('course-error-toast'));
          $('#course-error-body').text(error.responseJSON.non_field_errors.join(', '));
          toast.show();
          console.log(error);
        }
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
        const seasonSelect = $('#season-select');
        const seasonYear = seasonSelect[0].options[seasonSelect[0].selectedIndex].innerHTML;
        modalBody.textContent = `Etes-vous sur.e de vouloir supprimer la saison ${seasonYear} ainsi que ses cours associés ?`;
        url = seasonsUrl + seasonSelect.val() + '/';
      }
      $(document).on('click', '#delete-btn', function(){
        $.ajax({
          url: url,
          type: 'DELETE',
          headers: { 'X-CSRFToken': csrftoken },
          mode: 'same-origin',
          success: () => {
            location.reload();
          },
          error: (error) => {
            showToast(DEFAULT_ERROR);
            console.log(error);
          }
        });
      });
    });
  }
}

function showToast(text) {
  const toast = bootstrap.Toast.getOrCreateInstance(document.getElementById('course-error-toast'));
  $('#course-error-body').text(`${text} ${ERROR_SUFFIX}`);
  toast.show();
}
