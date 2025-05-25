let checkout;
$(document).ready(() => {
	initCheckout();
});

async function initCheckout() {
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
			let details = '<strong>Details:</strong><ul>' + payment.due_detail.map(t => `<li>${t}</li>`).join('');
			if (payment.sport_pass_count > 0) {
				details += `<li>${payment.sport_pass_count} Pass Sport: -${payment.sport_pass_amount}€</li>`;
			}
			if (payment.paid > payment.sport_pass_amount) {
				details += `<li>Déjà payé: -${payment.paid - payment.sport_pass_amount}€</li>`;
			}
			details += '</ul>';
			document.getElementById('checkout-details').innerHTML = details;
			document.getElementById('checkout-due').innerHTML = `<strong>Somme dûe:</strong> ${payment.due - payment.paid + payment.refund}€`;
		},
		error: (error) => {
			showToast('Impossible de récupérer vos informations pour le moment.');
			console.log(error);
		}
	});
}
