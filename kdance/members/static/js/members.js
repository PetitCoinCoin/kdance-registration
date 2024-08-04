$(document).ready(() => {
  displayPayments();
  initCheckPayment();
  handleCheckPayment();
  handleCourseUpdate();
  getSeasons();
  updateMember();
  const seasonSelect = document.querySelector('#season-select');
  seasonSelect.addEventListener('change', () =>
    onSeasonChange(seasonSelect.value)
  );
});

function populateMonths(itemId) {
  monthSelectAdd = $(itemId);
  for (let key in MONTH) {
    monthSelectAdd.append($('<option>', { value: key, text: MONTH[key] }));
  }
}

function handleCourseUpdate() {
  // Course removal
  $('#cancel-course-btn').on('click', () => {
    $('#course-list').empty();
    Object.values($('#courses-select option:selected')).slice(0, -2).map((option) => {
      $('#course-list').append($('<li>', { class: 'list-group-item', text: option.text }));
    });
  });
  $('#delete-btn').on('click', () => {
    patchMemberCoursesActions($('#delete-btn').data('memberId'), "remove");
  });
  // Course addition
  $('#add-course-btn').on('click', () => {
    $('#add-courses-select').empty();
    $.ajax({
      url: coursesUrl + `?season=${$('#season-select').val()}`,
      type: 'GET',
      success: (data) => {
        const activeCourses = Object.values($('#courses-select option:enabled')).slice(0, -2).map(o => parseInt(o.value));
        data.map(course => {
          const startHour = course.start_hour.split(':');
          const label = `${course.name}, ${WEEKDAY[course.weekday]} ${startHour[0]}h${startHour[1]}`;
          $('#add-courses-select').append($('<option>', { value: course.id, text: label, disabled: activeCourses.indexOf(course.id) >= 0 }));
        });
      },
      error: (error) => {
        showToast('Impossible de récupérer les cours de la saison.');
        console.log(error);
      }
    });
  });
  $('#add-btn').on('click', () => {
    patchMemberCoursesActions($('#add-btn').data('memberId'), "add");
  });
}

function displayPayments() {
  const cashSwitch = document.querySelector('#cash-switch');
  cashSwitch.addEventListener('change', () => {
    $('#cash-div').attr('hidden', !$('#cash-switch').is(':checked'));
  });
  const checkSwitch = document.querySelector('#check-switch');
  checkSwitch.addEventListener('change', () => {
    $('#check-div').attr('hidden', !$('#check-switch').is(':checked'));
  });
  const ancvSwitch = document.querySelector('#ancv-switch');
  ancvSwitch.addEventListener('change', () => {
    $('#ancv-div').attr('hidden', !$('#ancv-switch').is(':checked'));
  });
  const passSwitch = document.querySelector('#pass-switch');
  passSwitch.addEventListener('change', () => {
    $('#pass-div').attr('hidden', !$('#pass-switch').is(':checked'));
  });
  const couponSwitch = document.querySelector('#coupon-switch');
  couponSwitch.addEventListener('change', () => {
    $('#coupon-div').attr('hidden', !$('#coupon-switch').is(':checked'));
  });
  const otherSwitch = document.querySelector('#other-switch');
  otherSwitch.addEventListener('change', () => {
    $('#other-div').attr('hidden', !$('#other-switch').is(':checked'));
  });
  const refundSwitch = document.querySelector('#refund-switch');
  refundSwitch.addEventListener('change', () => {
    $('#refund-div').attr('hidden', !$('#refund-switch').is(':checked'));
  });
  const specialSwitch = document.querySelector('#special-discount-switch');
  specialSwitch.addEventListener('change', () => {
    $('#special-discount-div').attr('hidden', !$('#special-discount-switch').is(':checked'));
  });
}

function initCheckPayment() {
  const checkParent = document.querySelector('#check-div');
  const checkTemplate = document.querySelector('#check-template');
  for (let i = 0; i < CHECK_NUMBER; i++) {
    const clone = checkTemplate.content.cloneNode(true);
    const items = clone.querySelectorAll('.form-outline');
    for (let k = 0; k < items.length; k++) {
      items[k].children[0].htmlFor += i;
      items[k].children[1].id += i;
    }
    // Add button except for last
    if (i < CHECK_NUMBER - 1) {
      const addTemplate = document.querySelector('#add-check-template');
      const addClone = addTemplate.content.cloneNode(true);
      let addButton = addClone.querySelector('button');
      addButton.id += `add-check-${i}`;
      clone.querySelectorAll('.row')[1].appendChild(addClone);
    }
    // Delete button + hidden except for first
    if (i > 0) {
      const removeTemplate = document.querySelector('#remove-check-template');
      const removeClone = removeTemplate.content.cloneNode(true);
      let removeButton = removeClone.querySelector('button');
      removeButton.id += `remove-check-${i}`;
      removeButton.dataset.bsCnumber = i;
      clone.querySelectorAll('.row')[1].appendChild(removeClone);
      clone.querySelectorAll('div')[0].id = `check-item-${i}`;
      clone.querySelectorAll('div')[0].hidden = true;
    }
    checkParent.appendChild(clone);
    populateMonths(`#payment-check-month-${i}`);
  }
}

function handleCheckPayment() {
  for (let i = 0; i < CHECK_NUMBER - 1; i++) {
    $(`#add-check-${i}`).on('click', () => {
      $(`#check-item-${i + 1}`).attr('hidden', false);
      $(`#payment-check-name-${i + 1}`).val($(`#payment-check-name-${i}`).val());
      $(`#payment-check-bank-${i + 1}`).val($(`#payment-check-bank-${i}`).val());
    });
  }
  for (let i = 1; i < CHECK_NUMBER; i++) {
    $(`#remove-check-${i}`).on('click', () => {
      $(`#payment-check-name-${i}`).val('');
      $(`#payment-check-bank-${i}`).val('');
      $(`#payment-check-number-${i}`).val('');
      $(`#payment-check-amount-${i}`).val('');
      $(`#payment-check-month-${i}`).val('0');
      $(`#check-item-${i}`).attr('hidden', true);
    });
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
          getMembers(season.id);
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

function onSeasonChange(seasonId) {
  getMembers(seasonId);
}

function courseFormatter(value) {
  return value.join('<br>')
}

function actionFormatter(value, row) {
  return `<button class="btn btn-outline-info btn-sm" memberId="${row.id}" paymentId="${row.payment.id}" type="button" data-bs-toggle="modal" data-bs-target="#member-modal"><i class="bi-pencil-fill"></i></button>`;
}

function getMembers(seasonId) {
  $.ajax({
    url: membersUrl + `?season=${seasonId}`,
    type: 'GET',
    success: (data) => {
      // Bootstrap table not initialised
      if (document.querySelector('#members-table').className === '') {
        $('#members-table').bootstrapTable({
          ...COMMON_TABLE_PARAMS,
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
            field: 'courses',
            title: 'Cours',
            searchable: true,
            sortable: true,
            visible: false,
            formatter: courseFormatter,
          }, {
            field: 'documents.authorise_photos',
            title: 'Autorisation photos',
            searchable: true,
            sortable: true,
          }, {
            field: 'documents.authorise_emergency',
            title: 'Autorisation parentale',
            searchable: true,
            sortable: true,
          }, {
            field: 'documents.medical_document',
            title: 'Doc médical',
            searchable: true,
            sortable: true,
            cellStyle: function (value) {
              return {
                classes: value == 'Manquant' ? 'bg-alert' : 'bg-info'
              };
            }
          }, {
            field: 'solde',
            title: 'Solde dû (€)',
            searchable: true,
            sortable: true,
            cellStyle: function (value) {
              return {
                classes: value > 0 ? 'bg-alert' : value < 0 ? 'bg-warning' : 'bg-info'
              };
            }
          }, {
            field: 'payment.comment',
            title: 'Commentaire',
            searchable: true,
            sortable: false,
            visible: false,
          }, {
            field: 'operate',
            title: 'Modifier',
            align: 'center',
            clickToSelect: false,
            formatter: actionFormatter,
          }],
          data: data.map((m) => {
            return {
              ...m,
              courses: m.active_courses.map((c) => `- ${c.name}, ${WEEKDAY[c.weekday]}`).concat(m.cancelled_courses.map((c) => `- ${c.name}, ${WEEKDAY[c.weekday]} (Annulé)`)),
              solde: m.payment.due - m.payment.paid + m.payment.refund,
              documents: m.documents ? {
                ...m.documents,
                authorise_photos: m.documents.authorise_photos ? 'Oui' : 'Non',
                authorise_emergency: m.documents.authorise_emergency ? 'Oui' : 'Non',
              } : null,
            }
          })
        });
        $('input[type=search]').attr('placeholder', 'Rechercher');
        // Already initialised
      } else {
        $('#members-table').bootstrapTable('load', data.map((m) => {
          return {
            ...m,
            courses: m.active_courses.map((c) => `- ${c.name}, ${WEEKDAY[c.weekday]}`).concat(m.cancelled_courses.map((c) => `- ${c.name}, ${WEEKDAY[c.weekday]} (Annulé)`)),
            solde: m.payment.due - m.payment.paid,
            documents: m.documents ? {
              ...m.documents,
              authorise_photos: m.documents.authorise_photos ? 'Oui' : 'Non',
              authorise_emergency: m.documents.authorise_emergency ? 'Oui' : 'Non',
            } : null,
          }
        }));
      }
    },
    error: (error) => {
      showToast('Impossible de récupérer les adhérents de la saison.');
      console.log(error);
    }
  });
}

function getMember(memberId) {
  $('.invalid-feedback').removeClass('d-inline');
  $.ajax({
    url: membersUrl + memberId + '/',
    type: 'GET',
    success: (data) => {
      $('#member-modal-title').html(`Mettre à jour les données de ${data.first_name} ${data.last_name}`);
      $('#member-name').text(`${data.first_name} ${data.last_name}`);  // Deletion modale
      $('#doc-select').val(data.documents?.medical_document || "Manquant");
      $('#authorise-photos').prop('checked', data.documents?.authorise_photos || false);
      $('#authorise-emergency').prop('checked', data.documents?.authorise_emergency || true);

      // Payment
      $('#payment-cash').val(data.payment.cash);
      const withCash = !(data.payment.cash === null || data.payment.cash === 0);
      $('#cash-div').attr('hidden', !withCash);
      $('#cash-switch').prop('checked', withCash);

      $('#payment-pass-code').val(data.sport_pass?.code || '');
      $('#payment-pass-amount').val(data.sport_pass?.amount || 50);
      const withPass = !(data.sport_pass === null || data.sport_pass?.code === null || data.sport_pass?.code === '');
      $('#pass-div').attr('hidden', !withPass);
      $('#pass-switch').prop('checked', withPass);

      $('#payment-coupon-count').val(data.payment.sport_coupon?.count || '');
      $('#payment-coupon-amount').val(data.payment.sport_coupon?.amount || '');
      const withCoupon = data.payment.sport_coupon !== null && !(data.payment.sport_coupon.count === null || data.payment.sport_coupon.amount === 0);
      $('#coupon-div').attr('hidden', !withCoupon);
      $('#coupon-switch').prop('checked', withCoupon);

      $('#payment-ancv-count').val(data.payment.ancv?.count || '');
      $('#payment-ancv-amount').val(data.payment.ancv?.amount);
      const withAncv = data.payment.ancv !== null && !(data.payment.ancv.amount === null || data.payment.ancv.amount === 0);
      $('#ancv-div').attr('hidden', !withAncv);
      $('#ancv-switch').prop('checked', withAncv);

      $('#payment-other-amount').val();
      $('#payment-other-comment').val(data.payment.other_payment?.comment);
      $('#payment-other-amount').val(data.payment.other_payment?.amount);
      const withOther = !(data.payment.other_payment === null || data.payment.other_payment?.amount === null || data.payment.other_payment?.amount === 0);
      $('#other-div').attr('hidden', !withOther);
      $('#other-switch').prop('checked', withOther);

      $('#comment').val(data.payment.comment);
      $('#payment-refund').val(data.payment.refund);
      const withRefund = !(data.payment.refund === null || data.payment.refund === 0);
      $('#refund-div').attr('hidden', !withRefund);
      $('#refund-switch').prop('checked', withRefund);

      $('#payment-special-discount').val(data.payment.special_discount);
      const withSpecial = !(data.payment.special_discount === null || data.payment.special_discount === 0);
      $('#special-discount-div').attr('hidden', !withSpecial);
      $('#special-discount-switch').prop('checked', withSpecial);

      for (let i = 0; i < CHECK_NUMBER; i++) {
        $(`#payment-check-name-${i}`).val(i < data.payment.check_payment.length ? data.payment.check_payment[i].name : '');
        $(`#payment-check-bank-${i}`).val(i < data.payment.check_payment.length ? data.payment.check_payment[i].bank : '');
        $(`#payment-check-number-${i}`).val(i < data.payment.check_payment.length ? data.payment.check_payment[i].number : '');
        $(`#payment-check-amount-${i}`).val(i < data.payment.check_payment.length ? data.payment.check_payment[i].amount : '');
        $(`#payment-check-month-${i}`).val(i < data.payment.check_payment.length ? data.payment.check_payment[i].month : '0');
        $(`#check-item-${i}`).attr('hidden', i >= data.payment.check_payment.length);
      }
      const withCheck = data.payment.check_payment.length > 0;
      $('#check-div').attr('hidden', !withCheck);
      $('#check-switch').prop('checked', withCheck);

      // Courses
      $('#member-courses-section').data('memberId', memberId);
      $('#courses-select').empty();
      data.active_courses.map((course) => {
        const startHour = course.start_hour.split(':');
        const label = `${course.name}, ${WEEKDAY[course.weekday]} ${startHour[0]}h${startHour[1]}`;
        $('#courses-select').append($('<option>', { value: course.id, text: label }));
      });
      data.cancelled_courses.map((course) => {
        const startHour = course.start_hour.split(':');
        const label = `(Annulé) ${course.name}, ${WEEKDAY[course.weekday]} ${startHour[0]}h${startHour[1]}`;
        $('#courses-select').append($('<option>', { value: course.id, text: label, disabled: true }));
      });
      $('#cancel-refund').val(data.cancel_refund);
      if (data.cancelled_courses.length > 0) {
        $('#cancelled-courses-div').show();
        $('#cancelled-courses-div span').text(data.cancel_refund);
      } else {
        $('#cancelled-courses-div').hide();
      }
    },
    error: (error) => {
      showToast('Impossible de récupérer les informations de cet adhérent.');
      console.log(error);
    }
  });
}

function updateMember() {
  const memberModal = document.getElementById('member-modal');
  if (memberModal) {
    $('#member-modal').on('show.bs.modal', function (event) {
      const button = event.relatedTarget;
      let memberId = button.getAttribute('memberId');
      const paymentId = button.getAttribute('paymentId');
      if (memberId === null) {
        memberId = $('#add-btn').data('memberId');
      }
      getMember(memberId);
      $('#form-member').data('memberId', memberId);
      $('#form-member').data('paymentId', paymentId);
      $('#add-btn').data('memberId', memberId);
      $('#cancel-btn').data('memberId', memberId);
    });
    $('#member-modal').on('submit', '#form-member', function (event) {
      event.preventDefault();
      const memberId = $(this).data('memberId');
      const paymentId = $(this).data('paymentId');
      patchMember(memberId, paymentId, event);
    })
  }
}

function patchMember(memberId, paymentId, event) {
  $('.invalid-feedback').removeClass('d-inline');
  // PATCH member first
  const memberData = {
    documents: {
      medical_document: $('#doc-select').val(),
      authorise_photos: $('#authorise-photos').is(':checked'),
      authorise_emergency: $('#authorise-emergency').is(':checked'),
    },
  };
  if ($('#payment-pass-code').val() !== '') {
    memberData.sport_pass = {
      code: $('#payment-pass-code').val(),
      amount: $('#payment-pass-amount').val(),
    };
  }
  $.ajax({
    url: membersUrl + memberId + '/',
    type: 'PATCH',
    contentType: 'application/json',
    headers: { 'X-CSRFToken': csrftoken },
    mode: 'same-origin',
    data: JSON.stringify(memberData),
    dataType: 'json',
    success: () => {
      // PATCH payment
      let paymentData = {
        cash: $('#payment-cash').val() || 0,
        ancv: {
          amount: $('#payment-ancv-amount').val() || 0,
          count: $('#payment-ancv-count').val() || 0,
        },
        other_payment: {
          amount: $('#payment-other-amount').val() || 0,
          comment: $('#payment-other-comment').val() || "A préciser",
        },
        sport_coupon: {
          amount: $('#payment-coupon-amount').val() || 0,
          count: $('#payment-coupon-count').val() || 0,
        },
        comment: $('#comment').val(),
        refund: $('#payment-refund').val() || 0,
        special_discount: $('#payment-special-discount').val() || 0,
      };
      var checks = [];
      for (let i = 0; i < CHECK_NUMBER; i++) {
        if ($(`#payment-check-amount-${i}`).val() !== '' || $(`#payment-check-number-${i}`).val() !== '') {
          checks.push({
            name: $(`#payment-check-name-${i}`).val(),
            bank: $(`#payment-check-bank-${i}`).val(),
            number: $(`#payment-check-number-${i}`).val(),
            amount: $(`#payment-check-amount-${i}`).val(),
            month: $(`#payment-check-month-${i}`).val(),
          });
        }
      }
      paymentData.check_payment = checks;
      $.ajax({
        url: paymentssUrl + paymentId + '/',
        type: 'PATCH',
        contentType: 'application/json',
        headers: { 'X-CSRFToken': csrftoken },
        mode: 'same-origin',
        data: JSON.stringify(paymentData),
        dataType: 'json',
        success: () => {
          event.currentTarget.submit();
        },
        error: (error) => {
          if (!error.responseJSON) {
            showToast('Une erreur est survenue lors de la mise à jour du paiement.');
            console.log(error);
          } else {
            const toast = bootstrap.Toast.getOrCreateInstance(document.getElementById('member-error-toast'));
            $('#member-error-body').text('Il y a un souci au niveau des paiements. Veuillez vérifier les informations.');
            toast.show();
          }
          if (error.responseJSON && error.responseJSON.ancv) {
            if(error.responseJSON.ancv.amount) {
              $('#invalid-ancv-amount').html(error.responseJSON.ancv.amount[0]);
              $('#invalid-ancv-amount').addClass('d-inline');
            }
            if(error.responseJSON.ancv.count) {
              $('#invalid-ancv-count').html(error.responseJSON.ancv.count[0]);
              $('#invalid-ancv-count').addClass('d-inline');
            }
          }
          if (error.responseJSON && error.responseJSON.other_payment) {
            if(error.responseJSON.other_payment.amount) {
              $('#invalid-other-amount').html(error.responseJSON.other_payment.amount[0]);
              $('#invalid-other-amount').addClass('d-inline');
            }
            if(error.responseJSON.other_payment.comment) {
              $('#invalid-other-comment').html(error.responseJSON.other_payment.comment[0]);
              $('#invalid-other-comment').addClass('d-inline');
            }
          }
          if (error.responseJSON && error.responseJSON.sport_coupon) {
            if(error.responseJSON.sport_coupon.amount) {
              $('#invalid-coupon-amount').html(error.responseJSON.sport_coupon.amount[0]);
              $('#invalid-coupon-amount').addClass('d-inline');
            }
            if(error.responseJSON.sport_coupon.count) {
              $('#invalid-coupon-count').html(error.responseJSON.sport_coupon.count[0]);
              $('#invalid-coupon-count').addClass('d-inline');
            }
          }
          if (error.responseJSON && error.responseJSON.check_payment) {
            for (let i = 0; i < CHECK_NUMBER; i++) {
              if (error.responseJSON.check_payment[i].name) {
                $(`#payment-check-name-${i} + div`).html(error.responseJSON.check_payment[i].name[0]);
                $(`#payment-check-name-${i} + div`).addClass('d-inline');
              }
              if (error.responseJSON.check_payment[i].bank) {
                $(`#payment-check-bank-${i} + div`).html(error.responseJSON.check_payment[i].bank[0]);
                $(`#payment-check-bank-${i} + div`).addClass('d-inline');
              }
              if (error.responseJSON.check_payment[i].number) {
                $(`#payment-check-number-${i} + div`).html(error.responseJSON.check_payment[i].number[0]);
                $(`#payment-check-number-${i} + div`).addClass('d-inline');
              }
              if (error.responseJSON.check_payment[i].amount) {
                $(`#payment-check-amount-${i} + div`).html(error.responseJSON.check_payment[i].amount[0]);
                $(`#payment-check-amount-${i} + div`).addClass('d-inline');
              }
              if (error.responseJSON.check_payment[i].month) {
                $(`#payment-check-month-${i} + div`).html('Veuiller sélectionner un mois');
                $(`#payment-check-month-${i} + div`).addClass('d-inline');
              }
            }
          }
        }
      });
    },
    error: (error) => {
      let errorMessage = '';
      if (!error.responseJSON) {
        errorMessage += `${DEFAULT_ERROR} Impossible de mettre à jour les informations. `;
      }
      if (error.responseJSON && error.responseJSON.documents?.medical_document) {
        errorMessage += `Document médical: ${error.responseJSON.documents?.medical_document[0]} `;
      }
      if (error.responseJSON && error.responseJSON.documents?.authorise_photos) {
        errorMessage += `Autorisation photos: ${error.responseJSON.documents?.authorise_photos[0]} `;
      }
      if (error.responseJSON && error.responseJSON.documents?.authorise_emergency) {
        errorMessage += `Autorisation d'urgence: ${error.responseJSON.documents?.authorise_emergency[0]} `;
      }
      showToast(errorMessage);
      console.log(error);
    }
  });
}

function patchMemberCoursesActions(memberId, action) {
  let data = {
    courses: action === "add" ? $('#add-courses-select').val() : $('#courses-select').val(),
  };
  if (action === 'remove') {
    data['cancel_refund'] = $('#cancel-refund').val();
  }
  $.ajax({
    url: membersUrl + memberId + '/courses/' + action + '/',
    type: 'PATCH',
    contentType: 'application/json',
    headers: { 'X-CSRFToken': csrftoken },
    mode: 'same-origin',
    data: JSON.stringify(data),
    dataType: 'json',
    success: () => {},
    error: (error) => {
      if (!error.responseJSON) {
        showToast(DEFAULT_ERROR);
        console.log(error);
      }
      if (error.responseJSON && error.responseJSON.cancel_refund) {
        $('#invalid-cancel-refund').html(error.responseJSON.cancel_refund[0]);
        $('#invalid-cancel-refund').addClass('d-inline');
      }
    }
  });
}

function showToast(text) {
  const toast = bootstrap.Toast.getOrCreateInstance(document.getElementById('member-error-toast'));
  $('#member-error-body').text(`${text} ${ERROR_SUFFIX}`);
  toast.show();
}
