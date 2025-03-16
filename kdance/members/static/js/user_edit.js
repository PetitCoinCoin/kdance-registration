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
      }
    });
  });
}
