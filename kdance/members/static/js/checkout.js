/************************************************************************************/
/* Copyright 2024, 2025 Andréa Marnier                                              */
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
