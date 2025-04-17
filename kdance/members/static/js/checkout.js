$(document).ready(() => {
	fetchDetails();
});

function fetchDetails() {
	$.ajax({
		url: userMeUrl,
		type: 'GET',
		success: (data) => {
			const payments = data.payment.filter(p => p.season.is_current);
			if (payments.length !== 1) {
				document.getElementById('checkout-details').innerHTML = 'Il semble qu\'il y ait un souci avec votre compte. Merci de contacter <a href="mailto:tech@association-kdance.fr">tech@association-kdance.fr</a>';
				return
			}
			const payment = payments[0];
			let details = '<strong>Details:</strong><ul>' + payment.due_detail.map(t => `<li>${t}</li>`).join('') + '</ul>';
			document.getElementById('checkout-details').innerHTML = details;
		},
		error: (error) => {
			showToast('Impossible de récupérer vos informations pour le moment.');
			console.log(error);
		}
	});
}

function showToast(text) {
	const toast = bootstrap.Toast.getOrCreateInstance(document.getElementById('checkout-error-toast'));
	$('#checkout-error-body').text(`${text} ${ERROR_SUFFIX}`);
	toast.show();
}
