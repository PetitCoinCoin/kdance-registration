$(document).ready(() => {
  getUser();
  patchUser();
});

function getUser() {
  $.ajax({
    url: userMeUrl,
    type: 'GET',
    success: (data) => {
      $('#edit-me-firstname').val(data.first_name);
      $('#edit-me-lastname').val(data.last_name);
      $('#edit-me-email').val(data.email);
      $('#edit-me-phone').val(data.profile.phone);
      $('#edit-me-address').val(data.profile.address);
      $('#edit-me-postal-code').val(data.profile.postal_code);
      $('#edit-me-city').val(data.profile.city);
    },
    error: (error) => {
      showToast('Impossible de récupérer vos informations pour le moment.');
      console.log(error);
    }
  });
}

function patchUser() {
  $('#form-me').submit((event) => {
    $('.invalid-feedback').removeClass('d-inline');
    event.preventDefault();
    const data = {
      first_name: $('#edit-me-firstname').val(),
      last_name: $('#edit-me-lastname').val(),
      username: $('#edit-me-email').val().toLowerCase(),
      email: $('#edit-me-email').val().toLowerCase(),
      profile: {
        phone: $('#edit-me-phone').val(),
        address: $('#edit-me-address').val(),
        postal_code: $('#edit-me-postal-code').val(),
        city: $('#edit-me-city').val(),
      }
    };
    $.ajax({
      url: userMeUrl,
      type: 'PATCH',
      contentType: 'application/json',
      headers: { 'X-CSRFToken': csrftoken },
      mode: 'same-origin',
      data: JSON.stringify(data),
      dataType: 'json',
      success: () => {
        event.currentTarget.submit();
        window.location.replace('/');
      },
      error: (error) => {
        if (!error.responseJSON) {
          showToast('Une erreur est survenue lors de la mise à jour de vos informations.');
          console.log(error);
        }
        if (error.responseJSON && error.responseJSON.profile && error.responseJSON.profile.phone) {
          $('#invalid-edit-me-phone').html(error.responseJSON.profile.phone[0] + ' Format attendu: 0123456789.');
          $('#invalid-edit-me-phone').addClass('d-inline');
        }
        if (error.responseJSON && error.responseJSON.email) {
          $('#invalid-edit-me-email').html(error.responseJSON.email[0]);
          $('#invalid-edit-me-email').addClass('d-inline');
        }
        if (error.responseJSON && error.responseJSON.address) {
          $('#invalid-edit-me-address').html(error.responseJSON.address[0]);
          $('#invalid-edit-me-address').addClass('d-inline');
        }
        if (error.responseJSON && error.responseJSON.postal_code) {
          $('#invalid-edit-me-postal-code').html(error.responseJSON.postal_code[0]);
          $('#invalid-edit-me-postal-code').addClass('d-inline');
        }
        if (error.responseJSON && error.responseJSON.city) {
          $('#invalid-edit-me-city').html(error.responseJSON.city[0]);
          $('#invalid-edit-me-city').addClass('d-inline');
        }
      }
    });
  });
}
