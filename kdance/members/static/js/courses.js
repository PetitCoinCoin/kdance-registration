/************************************************************************************/
/* Copyright 2024 - present, Andréa Marnier                                              */
/*                                                                                  */
/* This file is part of KDance registration.                                        */
/*                                                                                  */
/* KDance registration is free software: you can redistribute it and/or modify it   */
/* under the terms of the GNU Affero General Public License as published by the     */
/* Free Software Foundation, either version 3 of the License, or any later version. */
/*                                                                                  */
/* KDance registration is distributed in the hope that it will be useful, but       */
/* WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or    */
/* FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License      */
/* for more details.                                                                */
/*                                                                                  */
/* You should have received a copy of the GNU Affero General Public License along   */
/* with KDance registration. If not, see <https://www.gnu.org/licenses/>.           */
/************************************************************************************/

$(document).ready(() => {
  populateWeekdays();
  getSeasons();
  getSkills();
  getTeachers();
  createUpdateSeason();
  createUpdateTeacher();
  createUpdateCourse();
  copyCourseFromSeason();
  deleteItem();
  const seasonSelect = document.querySelector('#season-select');
  seasonSelect.addEventListener('change', () => {
    onSeasonChange(seasonSelect.value, (sId) => {
      getCourses(sId);
      getPreviousSeason(sId);
    })
  });
  document.querySelector('#course-teacher').addEventListener('change', () => {
    onTeacherChange();
  });
  $('#add-skill-btn').on('click', () => { postSkill(); });
  breadcrumbDropdownOnHover();
});

function populateWeekdays() {
  weekdaySelectAdd = $('#course-weekday');
  for (let key in WEEKDAY) {
    weekdaySelectAdd.append($('<option>', { value: key, text: WEEKDAY[key] }));
  }
}

function getSeasons() {
  getSeasonsWrapper((data) => {
    var urlParams = new URLSearchParams(window.location.search);
    data.map((season) => {
      let label = season.year;
      const selectedUrl = urlParams.get('season') === season.id.toString();
      if (season.is_current) {
        label += ' (en cours)';
      }
      if (selectedUrl || (urlParams.get('season') === null && season.is_current)) {
        getCourses(season.id);
        $('#copy-modal-title').html(`Ajouter des cours à la saison ${season.year}`);
      } else {
        $('#copy-season').append($('<option>', { value: season.id, text: season.year }));
      }
      $('#season-select').append($(
        '<option>',
        { value: season.id, text: label, selected: urlParams.get('season') !== null ? selectedUrl : season.is_current }
      ));
    });
  }, COURSES_TOAST_PREFIX);
}

function getSeason(season) {
  $('.invalid-feedback').removeClass('d-inline');
  $.ajax({
    url: seasonsUrl + season,
    type: 'GET',
    success: (data) => {
      $('#season-year').val(data.year);
      $('#season-current').prop('checked', data.is_current);
      $('#season-adhesion-fee').val(data.adhesion_fee);
      $('#season-discount-percent').val(data.discount_percent);
      $('#season-discount-limit').val(data.discount_limit);
      $('#season-pass-sport-amount').val(data.pass_sport_amount);
      $('#pre-signup-start').val(data.pre_signup_start);
      $('#pre-signup-end').val(data.pre_signup_end);
      $('#signup-start').val(data.signup_start);
      $('#signup-end').val(data.signup_end);
      $('#season-ffd-a-amount').val(data.ffd_a_amount);
      $('#season-ffd-b-amount').val(data.ffd_b_amount);
      $('#season-ffd-c-amount').val(data.ffd_c_amount);
      $('#season-ffd-d-amount').val(data.ffd_d_amount);
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
    $('.invalid-feedback').removeClass('d-inline');
    event.preventDefault();
    const data = {
      year: $('#season-year').val(),
      is_current: $('#season-current').is(':checked'),
      pre_signup_start: $('#pre-signup-start').val() !== '' ? $('#pre-signup-start').val() : undefined,
      pre_signup_end: $('#pre-signup-end').val() !== '' ? $('#pre-signup-end').val() : undefined,
      signup_start: $('#signup-start').val() !== '' ? $('#signup-start').val() : null,
      signup_end: $('#signup-end').val() !== '' ? $('#signup-end').val() : null,
      ffd_a_amount: $('#season-ffd-a-amount').val(),
      ffd_b_amount: $('#season-ffd-b-amount').val(),
      ffd_c_amount: $('#season-ffd-c-amount').val(),
      ffd_d_amount: $('#season-ffd-d-amount').val(),
    };
    if ($('#season-adhesion-fee').val() !== '') {
      data['adhesion_fee'] = $('#season-adhesion-fee').val();
    }
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
          showToast(DEFAULT_ERROR, COURSES_TOAST_PREFIX);
        }
        if (error.responseJSON.year) {
          $('#invalid-season-year').html(error.responseJSON.year[0] + ' Format attendu: XXXX-YYYY');
          $('#invalid-season-year').addClass('d-inline');
        }
        if (error.responseJSON.pre_signup_start) {
          $('#invalid-pre-signup-start').html(error.responseJSON.pre_signup_start[0]);
          $('#invalid-pre-signup-start').addClass('d-inline');
        }
        if (error.responseJSON.pre_signup_end) {
          $('#invalid-pre-signup-end').html(error.responseJSON.pre_signup_end[0]);
          $('#invalid-pre-signup-end').addClass('d-inline');
        }
        if (error.responseJSON.signup_start) {
          $('#invalid-signup-start').html(error.responseJSON.signup_start[0]);
          $('#invalid-signup-start').addClass('d-inline');
        }
        if (error.responseJSON.signup_end) {
          $('#invalid-signup-end').html(error.responseJSON.signup_end[0]);
          $('#invalid-signup-end').addClass('d-inline');
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
      success: () => {
        event.currentTarget.submit();
      },
      error: (error) => {
        showToast(DEFAULT_ERROR, COURSES_TOAST_PREFIX);
        console.log(error);
      }
    });
  });
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
  showLoader();
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
          rowStyle: function (row, index) {
            return {
              classes: row.waiting > 0 ? 'bg-alert' : 'bg-info'
            };
          },
          columns: [{
            field: 'name',
            title: 'Nom',
            searchable: true,
            sortable: true,
          }, {
            field: 'years',
            title: 'Années',
            searchable: false,
            sortable: true,
          }, {
            field: 'teacher.name',
            title: 'Professeur',
            searchable: true,
            sortable: true,
            visible: false,
          }, {
            field: 'skill.name',
            title: 'Discipline',
            searchable: true,
            sortable: true,
            visible: false,
          }, {
            field: 'capacity',
            title: 'Capacité',
            searchable: false,
            sortable: false,
          }, {
            field: 'is_complete',
            title: 'Complet',
            searchable: true,
            sortable: true,
            cellStyle: function (value) {
              return {
                classes: value == 'Oui' ? 'bg-warning' : ''
              };
            },
          }, {
            field: 'waiting',
            title: 'En attente',
            searchable: false,
            sortable: true,
            cellStyle: { css: { 'background-color': 'inherit !important' } },
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
              is_complete: c.is_complete ? 'Oui' : 'Non',
              slot: `${WEEKDAY[c.weekday]}, ${startHour[0]}h${startHour[1]}-${endHour[0]}h${endHour[1]}`,
              years: formatCourseYears(c)
            }
          })
        });
        // Already initialised
      } else {
        $('#courses-table').bootstrapTable('load', data.map(c => {
          const startHour = c.start_hour.split(':');
          const endHour = c.end_hour.split(':');
          return {
            ...c,
            price: c.price + '€',
            is_complete: c.is_complete ? 'Oui' : 'Non',
            slot: `${WEEKDAY[c.weekday]}, ${startHour[0]}h${startHour[1]}-${endHour[0]}h${endHour[1]}`,
            years: formatCourseYears(c)
          }
        }));
      }
    },
    error: (error) => {
      showToast('Impossible de récupérer les cours de la saison.', COURSES_TOAST_PREFIX);
      console.log(error);
    },
    complete: () => {
      hideLoader();
    }
  });
}

function getSkills() {
  $.ajax({
    url: skillsUrl,
    type: 'GET',
    success: (data) => {
      for (const skill of data) {
        const element = `<li class="form-check">
        <input type="checkbox" class="form-check-input" id="check-skill-${skill.id}" value="${skill.id}">
        <label class="form-check-label" for="skill-${skill.id}">${skill.name}</label>
      </li>`
        $('#teacher-skills-select').append(element);
      }
    },
    error: (error) => {
      showToast('Impossible de récupérer la liste des disciplines.', COURSES_TOAST_PREFIX);
      console.log(error);
    }
  });
}

function postSkill() {
  $.ajax({
    url: skillsUrl,
    type: 'POST',
    headers: { 'X-CSRFToken': csrftoken },
    mode: 'same-origin',
    dataType: 'json',
    data: { name: $('#new-skill-input').val() },
    success: (data) => {
      const element = `<li class="form-check">
      <input type="checkbox" class="form-check-input" id="check-skill-${data.id}" value="${data.id}">
      <label class="form-check-label" for="skill-${data.id}">${data.name}</label>
    </li>`
      $('#teacher-skills-select').append(element);
      $('#new-skill-input').val(undefined)
    },
    error: (error) => {
      if (!error.responseJSON) {
        showToast('Impossible d\'ajouter une nouvelle discipline.', COURSES_TOAST_PREFIX);
        console.log(error);
      }
      if (error.responseJSON && error.responseJSON.name) {
        showToast(error.responseJSON.name[0], COURSES_TOAST_PREFIX, false);
      }
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
      skillSelect = $('#course-skill');
      data.map((teacher) => {
        teacherSelect.append($('<option>', { value: teacher.id, text: teacher.name, skills: teacher.skills.map(s=> s.id) }));
        teacher.skills.map((skill) => {
          if (Array.from(skillSelect.prop('options')).map(o => parseInt(o.value)).indexOf(skill.id) < 0) {
            skillSelect.append($('<option>', { value: skill.id, text: skill.name }));
          }
        });
        const clone = teacherTemplate.content.cloneNode(true);
        let data = clone.querySelector('span');
        data.textContent = teacher.skills.length > 0 ? `${teacher.name} : ${teacher.skills.map(s => s.name).join(', ')}` : teacher.name;
        let avatar = clone.querySelector('img');
        avatar.src = `https://api.dicebear.com/8.x/thumbs/svg?seed=${teacher.name}&radius=50`;
        let buttons = clone.querySelectorAll('button');
        buttons[0].id = `edit-${teacher.id}-btn`;
        buttons[0].dataset.bsTname = teacher.name;
        buttons[0].dataset.bsTid = teacher.id;
        buttons[0].dataset.bsTskillids = teacher.skills.map(s => s.id);
        buttons[1].id = `delete-${teacher.id}-btn`;
        buttons[1].dataset.bsTname = teacher.name;
        buttons[1].dataset.bsTid = teacher.id;
        listParent.appendChild(clone);
      });
      onTeacherChange();
    },
    error: (error) => {
      showToast('Impossible de récupérer la liste des professeurs.', COURSES_TOAST_PREFIX);
      console.log(error);
    }
  });
}

function onTeacherChange() {
  const teacherskills = $('#course-teacher')[0].selectedOptions[0].getAttribute('skills');
  const skills = !! teacherskills ? teacherskills.split(',').map(s => parseInt(s)) : [];
  for (var skill of $('#course-skill').prop('options')) {
    if (skills.indexOf(parseInt(skill.value)) < 0) {
      skill.disabled = true;
      skill.selected = false;
    } else {
      skill.disabled = false;
    }
  }
}

function createUpdateTeacher() {
  const teacherModal = document.getElementById('teacher-modal');
  if (teacherModal) {
    teacherModal.addEventListener('show.bs.modal', event => {
      const button = event.relatedTarget;
      const teacher = button.getAttribute('data-bs-Tid');
      const teacherName = button.getAttribute('data-bs-Tname');
      const teacherskills = button.getAttribute('data-bs-Tskillids');
      const skills = !! teacherskills ? teacherskills.split(',') : [];
      $('.invalid-feedback').removeClass('d-inline');
      if (teacher !== null) {
        $('#teacher-modal-title').html('Modifier un professeur');
        $('#teacher-btn').html('Modifier');
        $('#teacher-name').val(teacherName);
        for (element of $('[id^=check-skill-]')) {
          element.checked = skills.indexOf(element.value) > -1;
        }
      } else {
        $('#teacher-modal-title').html('Ajouter un professeur');
        $('#teacher-btn').html('Ajouter');
        $('#teacher-name').val(undefined);
        for (element of $('[id^=check-skill-]')) {
          element.checked = false;
        }
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
    let skills = [];
    for (const element of $('[id^=check-skill-]')) {
      if (element.checked) {
        skills.push(parseInt(element.value));
      }
    }
    const data = {
      name: $('#teacher-name').val(),
      skills
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
        location.reload();
      },
      error: (error) => {
        if (!error.responseJSON) {
          showToast(DEFAULT_ERROR, COURSES_TOAST_PREFIX);
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
      $('#course-btn').on('click', () => {
        postOrPatchCourse(course);
      });
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
      onTeacherChange();
      $('#course-skill').val(data.skill?.id);
      $('#course-price').val(data.price);
      $('#course-weekday').val(data.weekday);
      $('#course-start').val(data.start_hour.substring(0, 5));
      $('#course-end').val(data.end_hour.substring(0, 5));
      $('#course-capacity').val(data.capacity);
      $('#course-max-year').val(data.max_year);
      $('#course-min-year').val(data.min_year ?? "");
    },
    error: (error) => {
      showToast('Impossible de récupérer les informations du cours.', COURSES_TOAST_PREFIX);
      console.log(error);
    }
  });
}

function postOrPatchCourse(course) {
  const method = course === null ? 'POST' : 'PATCH';
  const url = course === null ? coursesUrl : coursesUrl + course + '/';
  $('.invalid-feedback').removeClass('d-inline');
  const minYear = $('#course-min-year').val();
  const data = {
    name: $('#course-name').val(),
    teacher: $('#course-teacher').val(),
    skill: $('#course-skill').val(),
    season: $('#season-select').val(),
    price: $('#course-price').val(),
    weekday: $('#course-weekday').val(),
    start_hour: $('#course-start').val(),
    end_hour: $('#course-end').val(),
    capacity: $('#course-capacity').val(),
    max_year: $('#course-max-year').val(),
    min_year: minYear == "" ? null : minYear
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
      location.reload();
    },
    error: (error) => {
      if (!error.responseJSON) {
        showToast(DEFAULT_ERROR, COURSES_TOAST_PREFIX);
      }
      if (error.responseJSON && error.responseJSON.non_field_errors) {
        const toast = bootstrap.Toast.getOrCreateInstance(document.getElementById('course-error-toast'));
        $('#course-error-body').text(error.responseJSON.non_field_errors.join(', '));
        toast.show();
        console.log(error);
      }
      if (error.responseJSON && error.responseJSON.min_year) {
        $('#invalid-course-min-year').html(error.responseJSON.min_year[0]);
        $('#invalid-course-min-year').addClass('d-inline');
      }
      if (error.responseJSON && error.responseJSON.max_year) {
        $('#invalid-course-max-year').html(error.responseJSON.max_year[0]);
        $('#invalid-course-max-year').addClass('d-inline');
      }
    }
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
            showToast(DEFAULT_ERROR, COURSES_TOAST_PREFIX);
            console.log(error);
          }
        });
      });
    });
  }
}
