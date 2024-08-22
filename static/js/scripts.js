document.addEventListener('DOMContentLoaded', function() {
    // Show and hide popups
    const btnUpdate = document.getElementById('btnUpdate');
    const closeFormBtnPayment = document.getElementById('closeFormBtnPayment');
    const closeFlashPopup = document.getElementById('closeFlashPopup');
    const openFormBtn = document.getElementById('openFormBtn');
    const closeFormBtnOrder = document.getElementById('closeFormBtnOrder');
    const openInvoiceBtn = document.getElementById('openInvoiceBtn');
    const closeFormBtnInvoice = document.getElementById('closeFormBtnInvoice');
    const flashMessages = document.getElementById('flashMessages');
    const flashPopup = document.getElementById('flashPopup');

    if (btnUpdate) {
        btnUpdate.addEventListener('click', function() {
            const popupFormPayment = document.getElementById('popupFormPayment');
            if (popupFormPayment) {
                popupFormPayment.style.display = 'block';
            }
        });
    }

    if (closeFormBtnPayment) {
        closeFormBtnPayment.addEventListener('click', function() {
            const popupFormPayment = document.getElementById('popupFormPayment');
            if (popupFormPayment) {
                popupFormPayment.style.display = 'none';
            }
        });
    }

    if (closeFlashPopup) {
        closeFlashPopup.addEventListener('click', function() {
            if (flashPopup) {
                flashPopup.style.display = 'none';
            }
        });
    }

    if (openFormBtn) {
        openFormBtn.addEventListener('click', function() {
            const popupFormOrder = document.getElementById('popupFormOrder');
            if (popupFormOrder) {
                popupFormOrder.style.display = 'block';
            }
        });
    }

    if (closeFormBtnOrder) {
        closeFormBtnOrder.addEventListener('click', function() {
            const popupFormOrder = document.getElementById('popupFormOrder');
            if (popupFormOrder) {
                popupFormOrder.style.display = 'none';
            }
        });
    }

    // Handle flash message popup display
    if (flashMessages && flashMessages.innerHTML.trim() !== '') {
        if (flashPopup) {
            flashPopup.style.display = 'block';
        }
    }




    // Handle search form input and table update
    const form = document.getElementById('search-form');
    const clearBtn = document.getElementById('clrBtn');

    if (form) {
        form.addEventListener('input', (event) => {
            event.preventDefault(); // Prevent the form from submitting traditionally
            const formData = new FormData(form);

            fetch('/transactions', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                updateTable(data);
            })
            .catch(error => console.error('Error:', error));
        });
    }

    function updateTable(data) {
        const tableBody = document.querySelector('#all');
        if (tableBody) {
            tableBody.innerHTML = ''; // Clear existing rows

            data.orders_all.forEach(order => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${order.tranx_id}</td>
                    <td>${order.code}</td>
                    <td>${order.customer}</td>
                    <td>${order.brand}</td>
                    <td>${order.item_desc}</td>
                    <td>${order.pur_date}</td>
                    <td>${order.lay_terms}</td>
                    <td>${order.months_to_pay}</td>
                    <td>${order.balance}</td>
                    <td><span class="status ${order.pay_status.toLowerCase()}">${order.pay_status}</span></td>
                    <td><button class="button-update">Update</button></td>
                `;
                tableBody.appendChild(row);
            });
        }
    }

    // Handle clear button visibility
    function toggleClearButton() {
        const customer = document.getElementById('customer-tranx').value;
        const fromDate = document.getElementById('date-picker-from').value;
        const toDate = document.getElementById('date-picker-to').value;
        if (clearBtn) {
            clearBtn.style.display = customer ? 'block' : 'none';
        }
    }

    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            if (form) form.reset();
            if (clearBtn) clearBtn.style.display = 'none'; // Hide clear button
        });
    }

    // Initial check for clear button visibility
    toggleClearButton();

    // Handle quantity change
    const quantityInput = document.getElementById('quantity');
    if (quantityInput) {
        quantityInput.addEventListener('change', updateSellingPrice);
    }

    function updateSellingPrice() {
        const quantity = parseInt(quantityInput.value) || 0;
        const unitPrice = parseFloat(document.getElementById('unit-price').value) || 0;
        const totalPriceInput = document.getElementById('total-price');

        if (totalPriceInput) {
            totalPriceInput.value = (quantity * unitPrice).toFixed(2);
        }
    }
});

document.addEventListener('DOMContentLoaded', () => {
    const addRowButton = document.getElementById('addRowButton');
    const invoiceTableBody = document.getElementById('invoiceTableBody');
    
    const totalElement = document.querySelector('.invoice-total');

    
    addRowButton.addEventListener('click', (event) => {
        event.preventDefault(); // Prevent default link behavior

        // Create a new row element
        const newRow = document.createElement('tr');

        // Define the new row's content
        newRow.innerHTML = `
            <td>
                <div class="product-field">
                    <input type="text" name="brand_code[]" placeholder="Insert QR Code" required>
                </div>
            </td>
            <td>
                <div>
                    <input type="text" name="brand-inv[]" placeholder="Brand" required>
                </div>
            </td>
            <td>
                <div>
                    <input type="number" name="quantity[]" min="1" value="1" onchange="updateSellingPrice(this)">
                </div>
            </td>
            <td>
                <div>
                    <input type="number" name="invoice_product_price[]" placeholder="0.00" class="form-control">
                </div>
            </td>
            <td>
                <div>
                    <input type="text" name="desc[]" placeholder="Item Description" readonly>
                </div>
            </td>
            <td>
                <div>
                    <input type="text" name="invoice_product_sub[]" value="0.00" disabled class="form-control">
                </div>
            </td>
            <td>
                <div class="action-field">
                    <button class="button-delete" onclick="deleteRow(this)">Delete</button>
                </div>
            </td>
        `;

        // Append the new row to the table body
        invoiceTableBody.appendChild(newRow);
    });

            // Handle input blur event for brand code lookup
            invoiceTableBody.addEventListener('blur', (event) => {
                if (event.target && event.target.name === 'brand_code[]') {
                    const brandCodeInput = event.target;
                    const brandCode = brandCodeInput.value;

                    if (brandCode) {
                        fetch('/search_by_brand_code', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                            body: new URLSearchParams({ 'brand_code': brandCode })
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.error) {
                                alert(data.error);
                            } else {
                                const row = brandCodeInput.closest('tr');
                                row.querySelector('input[name="brand-inv[]"]').value = data.brand || '';
                                row.querySelector('input[name="desc[]"').value = data.description || '';
                                row.querySelector('input[name="invoice_product_price[]"]').value = data.price || '';
                                row.querySelector('input[name="invoice_product_sub[]"]').value = data.price || '';
                                updateGrandTotal();
                            }
                        })
                        .catch(error => console.error('Error fetching data:', error));
                    }
                }
            }, true);
        });

        function updateSellingPrice(input) {
            const row = input.closest('tr');
            const quantity = row.querySelector('input[name="quantity[]"]').value;
            const price = row.querySelector('input[name="invoice_product_price[]"]').value;
            const subtotal = quantity * price;
            row.querySelector('input[name="invoice_product_sub[]"]').value = subtotal.toFixed(2);
            updateGrandTotal();
        }



            // Function to delete a row
            function deleteRow(button) {
                const row = button.closest('tr');
                row.remove();
                updateGrandTotal();
            }

            const layawayTerms = {
                "8rageous": { months: 7, firstPay: 0.08 },
                "10rageous": { months: 9, firstPay: 0.1 },
                "20% 6 months": { months: 6, firstPay: 0.2 },
                "10% 10 months": { months: 8, firstPay: 0 },
                "14% 8 months": { months: 8, firstPay: 0.14 },
                "6 months": { months: 6, firstPay: 0 },
                "20% 8 months": { months: 8, firstPay: 0.2 },
                "10% 8 months": { months: 8, firstPay: 0.1 },
                "10% 6 months": { months: 6, firstPay: 0.1 },
                "10% 12 months": { months: 12, firstPay: 0.1 },
                "20% 10 months": { months: 10, firstPay: 0.2 },
                "12% 12 months": { months: 12, firstPay: 0.12 },
                "6% 12 months": { months: 12, firstPay: 0.06 },
                "20% 12 months": { months: 12, firstPay: 0.2 },
                "8% 8 months": { months: 8, firstPay: 0.08 },
                "11% 11 months": { months: 11, firstPay: 0.11 }
            };


            function updateGrandTotal() {
                let grandTotal = 0;
                const dpElement = document.getElementById('hidden_dp');
                const mpElement = document.getElementById('hidden_mp');
                const monthTerms = document.getElementById('months-topay');
                const subTotalElement =  document.getElementById('hidden_sub_total');
                const totalElement = document.getElementById('hidden_total_pay');
                const subtotalInputs = document.querySelectorAll('input[name="invoice_product_sub[]"]');

                
                subtotalInputs.forEach(input => {
                    grandTotal += parseFloat(input.value) || 0;
                });
                subTotalElement.value = grandTotal.toFixed(2);

                const downPayment = grandTotal * parseFloat(lwyTerm);
                const monthlyPayment = parseFloat(totalElement.value) / parseFloat(monthTerms.value);

                  // Update the text content of dpElement and totalElement
                  dpElement.value = downPayment.toFixed(2);
                  totalElement.value = (parseFloat(subTotalElement.value) - parseFloat(downPayment)).toFixed(2);
                  mpElement.value = (monthlyPayment).toFixed(2);
  
            }

            let lwyTerm =0;


            function updateLayawayDetails(selectElement) {
                const selectedTerm = selectElement.value;
                const monthsInput = document.getElementById('months-topay');
                
                if (layawayTerms[selectedTerm]) {
                    monthsInput.value = layawayTerms[selectedTerm].months;
                    lwyTerm = layawayTerms[selectedTerm].firstPay;
                } else {
                    monthsInput.value = '';
                    lwyTerm = 0;
                }
                updateGrandTotal();
            }


function toggleDropdown(event) {
    event.preventDefault(); // Prevent the default anchor click behavior

    const submenuContent = event.target.nextElementSibling;
    console.log(submenuContent); // Debugging line

    if (submenuContent.classList.contains('show')) {
        submenuContent.classList.remove('show');
    } else {
        document.querySelectorAll('.submenu-content').forEach(function(content) {
            content.classList.remove('show');
        });
        submenuContent.classList.add('show');
    }
}

function setDueDate() {
    const paymentDate = document.getElementById('date-picker-from').value;
    const nextDueDateInput = document.getElementById('date-picker-to');

    if (paymentDate) {
        const paymentDateObj = new Date(paymentDate);
        paymentDateObj.setDate(paymentDateObj.getDate() + 30);

        const year = paymentDateObj.getFullYear();
        const month = String(paymentDateObj.getMonth() + 1).padStart(2, '0');
        const day = String(paymentDateObj.getDate()).padStart(2, '0');

        nextDueDateInput.value = `${year}-${month}-${day}`;
    } else {
        nextDueDateInput.value = '';
    }
}


document.addEventListener('DOMContentLoaded', function() {
    // Define the required fields
    const requiredFields = [
        'invoice_id',
        'date-picker-from',
        'date-picker-to',
        'customer_name',
        'customer_address_1',
        'customer_city',
        'customer_postcode',
        'customer_email',
        'customer_province',
        'customer_country',
        'customer_phone',
        'layaway-terms',
        'months-topay',
        'payment-method'
    ];

    // Function to check if all required fields are filled
    function validateFields() {
        let allFilled = true;
        requiredFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                if (!field.value.trim()) {
                    allFilled = false;
                    field.style.border = '2px solid red'; // Highlight empty fields
                } else {
                    field.style.border = ''; // Remove highlight if field is filled
                }
            } else {
                console.log(`Field with ID ${fieldId} not found`);
            }
        });
        return allFilled;
    }

    // Function to show the popup with form data
    function showPopup() {
        // Check if all required fields are filled
        if (!validateFields()) {
            return; // Exit function to prevent showing the popup
        }

        // Fetch form data
        const invoiceId = document.getElementById('invoice_id')?.value || 'N/A';
        const invoiceDate = document.getElementById('date-picker-from')?.value || 'N/A';
        const dueDate = document.getElementById('date-picker-to')?.value || 'N/A';
        const customerName = document.getElementById('customer_name')?.value || 'N/A';
        const subTotalElement = document.getElementById('hidden_sub_total')?.value || '0';
        const dpElement = document.getElementById('hidden_dp')?.value || '0';
        const mpElement = document.getElementById('hidden_mp')?.value || '0';
        const monthTerm = document.getElementById('months-topay')?.value || '0';

        const customerAddress = [
            document.getElementById('customer_address_1')?.value || '',
            document.getElementById('customer_city')?.value || '',
            document.getElementById('customer_postcode')?.value || ''
        ].filter(Boolean).join(', ');
        const customerEmail = document.getElementById('customer_email')?.value || 'N/A';

        // Update popup with form data
        const popupInvoiceID = document.getElementById('popup_invoice_id');
        const popupInvoiceDate = document.getElementById('popup_invoice_date');
        const popupDueDate = document.getElementById('popup_due_date');
        const popupCustomerName = document.getElementById('popup_customer_name');
        const popupCustomerAddress = document.getElementById('popup_customer_address');
        const popupCustomerEmail = document.getElementById('popup_customer_email');

        if (popupInvoiceID) popupInvoiceID.textContent = invoiceId;
        if (popupInvoiceDate) popupInvoiceDate.textContent = invoiceDate;
        if (popupDueDate) popupDueDate.textContent = dueDate;
        if (popupCustomerName) popupCustomerName.textContent = customerName;
        if (popupCustomerAddress) popupCustomerAddress.textContent = customerAddress;
        if (popupCustomerEmail) popupCustomerEmail.textContent = customerEmail;

        // Extract table data
        const tableBody = document.getElementById('invoiceTableBody');
        const popupTableBody = document.getElementById('popupInvoiceTableBody');

        if (tableBody && popupTableBody) {
            // Clear previous rows
            popupTableBody.innerHTML = '';

            // Initialize totals
            let subTotal = 0;
            let dp = parseFloat(dpElement);
            let total = 0;
            let mp = parseFloat(mpElement);
            let mterms = parseFloat(monthTerm);
            let monthly =0;

            // Populate popup table with data
            Array.from(tableBody.rows).forEach(row => {
                if (row.cells.length < 5) return;

                const itemInput = row.cells[0]?.querySelector('input');
                const brandInput = row.cells[1]?.querySelector('input');
                const quantityInput = row.cells[2]?.querySelector('input');
                const priceInput = row.cells[3]?.querySelector('input');
                const descriptionInput = row.cells[4]?.querySelector('input');

                const item = itemInput ? itemInput.value.trim() : 'N/A';
                const brand = brandInput ? brandInput.value.trim() : 'N/A';
                const description = descriptionInput ? descriptionInput.value.trim() : 'N/A';
                const quantity = quantityInput ? parseInt(quantityInput.value, 10) : 0;
                const price = priceInput ? parseFloat(priceInput.value) : 0;

                if (item === '' || brand === '' || description === '' || quantity === 0 || price === 0) return;

                subTotal += price * quantity;
                total = subTotal - dp;
                monthly = mp / mterms;

                const newRow = document.createElement('tr');
                newRow.innerHTML = `
                    <td>${item}</td>
                    <td>${brand}</td>
                    <td>${description}</td>
                    <td>${quantity}</td>
                    <td>${price.toFixed(2)}</td>
                `;
                popupTableBody.appendChild(newRow);
            });

            // Update total price
            document.getElementById('popup_dp_price').textContent = '$' + dp.toFixed(2);
            document.getElementById('popup_subtotal_price').textContent = '$' + subTotal.toFixed(2);
            document.getElementById('popup_mp_price').textContent = '$' + monthly.toFixed(2);
            document.getElementById('popup_total_price').textContent = '$' + total.toFixed(2);
        } else {
            console.error('Table elements not found');
        }

        // Show the popup
        const popup = document.getElementById('popupFormInvoice');
        if (popup) {
            popup.style.display = 'block';
        } else {
            console.error('Popup element not found');
        }
    }

    // Add event listener to the "Open Invoice" button
    const openInvoiceBtn = document.getElementById('openInvoiceBtn');
    if (openInvoiceBtn) {
        openInvoiceBtn.addEventListener('click', function(event) {
            event.preventDefault(); // Prevent default form submission
            showPopup();
        });
    } else {
        console.error('Open Invoice button not found');
    }

    // Add event listener to the close button of the popup
    const closePopupBtn = document.getElementById('closeFormBtnInvoice');
    if (closePopupBtn) {
        closePopupBtn.addEventListener('click', function() {
            const popup = document.getElementById('popupFormInvoice');
            if (popup) {
                popup.style.display = 'none';
            } else {
                console.error('Popup element not found');
            }
        });
    } else {
        console.error('Close Popup button not found');
    }

    // Add event listener to the "Copy to Clipboard" button
    const copyInvoiceBtn = document.getElementById('copyInvoiceBtn');
    if (copyInvoiceBtn) {
        copyInvoiceBtn.addEventListener('click', function() {
            const invoiceDetails = document.querySelector('.invoice-box').innerText;
            navigator.clipboard.writeText(invoiceDetails)
                .then(() => {
                    alert('Invoice details copied to clipboard!');
                })
                .catch(err => {
                    console.error('Failed to copy: ', err);
                });
        });
    } else {
        console.error('Copy Invoice button not found');
    }
});

function showMessage(type, text) {
    const responseDiv = document.getElementById('response');
    const messageDiv = responseDiv.querySelector('.message');

    // Update the alert class based on the type
    responseDiv.className = `alert alert-${type}`;
    
    // Set the message text
    messageDiv.innerHTML = text;

    // Display the response div
    responseDiv.style.display = 'block';
}

document.querySelector('form').addEventListener('submit', function() {
    var subTotal = document.getElementById('sub_total').innerText;
    var downpayment = document.getElementById('dp').innerText;
    var total = document.getElementById('total_pay').innerText;

    // Ensure the hidden inputs are updated with the correct values
    document.getElementById('hidden_sub_total').value = parseFloat(subTotal.replace(/,/g, ''));
    document.getElementById('hidden_dp').value = parseFloat(downpayment.replace(/,/g, ''));
    document.getElementById('hidden_total_pay').value = parseFloat(total.replace(/,/g, ''));
});

document.addEventListener('DOMContentLoaded', function() {
    const openPopupBtn = document.getElementById('openCustomerBtn');
    const closePopupBtn = document.getElementById('closeCustomerBtn');
    const popup = document.getElementById('popupFormCustomer');
    const customerTableBody = document.querySelector('#customer_list tbody');
    const paginationControls = document.getElementById('paginationControls');

    let currentPage = 1;
    const perPage = 10; // Number of customers per page

    openPopupBtn.addEventListener('click', function(event) {
        event.preventDefault();
        loadCustomers(currentPage, perPage);
        popup.style.display = 'block';
    });

    closePopupBtn.addEventListener('click', function() {
        popup.style.display = 'none';
    });

    function loadCustomers(page, perPage) {
        fetch(`/get_customers?page=${page}&per_page=${perPage}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                alert("success");
                return response.json();

            })
            .then(data => {
                customerTableBody.innerHTML = ''; // Clear existing rows
                
                if (data.customers) {
                    data.customers.forEach(customer => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${customer.id}</td>
                            <td>${customer.name}</td>
                            <td>${customer.address}</td>
                            <td>${customer.email}</td>
                            <td>${customer.phone}</td>
                            <td><button class="selectCustomerBtn" data-id="${customer.id}" data-name="${customer.name}" data-address="${customer.address}" data-email="${customer.email}" data-phone="${customer.phone}">Select</button></td>
                        `;
                        customerTableBody.appendChild(row);
                    });

                    // Add event listeners for select buttons
                    const selectButtons = document.querySelectorAll('.selectCustomerBtn');
                    selectButtons.forEach(button => {
                        button.addEventListener('click', function() {
                            const customerId = this.getAttribute('data-id');
                            const customerName = this.getAttribute('data-name');
                            const customerAddress = this.getAttribute('data-address');
                            const customerEmail = this.getAttribute('data-email');
                            const customerPhone = this.getAttribute('data-phone');
                            selectCustomer(customerId, customerName, customerAddress, customerEmail, customerPhone);
                        });
                    });

                    // Setup pagination controls
                    setupPagination(data.pagination);
                } else {
                    console.error('No customer data found');
                }
            })
            .catch(error => console.error('Error loading customers:', error));
    }

    function setupPagination(pagination) {
        paginationControls.innerHTML = ''; // Clear existing pagination controls

        // Create previous button
        if (pagination.page > 1) {
            const prevButton = document.createElement('button');
            prevButton.textContent = 'Previous';
            prevButton.classList.add('pagination-btn');
            prevButton.addEventListener('click', function() {
                loadCustomers(pagination.page - 1, perPage);
                currentPage = pagination.page - 1;
            });
            paginationControls.appendChild(prevButton);
        }

        // Create page number buttons
        for (let i = 1; i <= pagination.total_pages; i++) {
            const pageButton = document.createElement('button');
            pageButton.textContent = i;
            pageButton.classList.add('pagination-btn');
            if (i === pagination.page) {
                pageButton.classList.add('active');
            }
            pageButton.addEventListener('click', function() {
                loadCustomers(i, perPage);
                currentPage = i;
            });
            paginationControls.appendChild(pageButton);
        }

        // Create next button
        if (pagination.page < pagination.total_pages) {
            const nextButton = document.createElement('button');
            nextButton.textContent = 'Next';
            nextButton.classList.add('pagination-btn');
            nextButton.addEventListener('click', function() {
                loadCustomers(pagination.page + 1, perPage);
                currentPage = pagination.page + 1;
            });
            paginationControls.appendChild(nextButton);
        }
    }

    function selectCustomer(customerId, customerName, customerAddress, customerEmail, customerPhone) {
        document.getElementById('customer_name').value = customerName;
        document.getElementById('selectedCustomerId').value = customerId;
        document.getElementById('customer_email').value = customerEmail;
        document.getElementById('customer_phone').value = customerPhone;

        // Split the address into components
        const addressParts = customerAddress.split(',');
        if (addressParts.length >= 5) {
            document.getElementById('customer_address_1').value = addressParts[0].trim();
            document.getElementById('customer_city').value = addressParts[1].trim();
            document.getElementById('customer_province').value = addressParts[2].trim();
            document.getElementById('customer_country').value = addressParts[3].trim();
            document.getElementById('customer_postcode').value = addressParts[4].trim();
        } else {
            console.error('Address format is incorrect');
        }
        
        popup.style.display = 'none';
    }
});

window.onload = function() {
    document.querySelector('form').reset();
};

function showTab(tabName) {
    // Hide all tab contents
    var tabContents = document.getElementsByClassName("tab-content");
    for (var i = 0; i < tabContents.length; i++) {
        tabContents[i].style.display = "none";
    }

    // Remove active class from all tab links
    var tabLinks = document.getElementsByClassName("tab-link");
    for (var i = 0; i < tabLinks.length; i++) {
        tabLinks[i].classList.remove("active");
    }

    // Show the current tab and add the active class to the clicked tab
    document.getElementById(tabName).style.display = "table-row-group"; // To display the table rows
    event.currentTarget.classList.add("active");
}

function formatDate(dateString) {
    // Create a Date object from the input string
    const date = new Date(dateString);
    
    // Check if the date is valid
    if (isNaN(date.getTime())) {
        console.error('Invalid date');
        return null;
    }

    // Format the date to YYYY-MM-DD
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are zero-based
    const day = String(date.getDate()).padStart(2, '0');

    return `${year}-${month}-${day}`;
}


function openPayFormForm(inv_id) {
    document.getElementById("invoiceNumber").value = "INV #" + inv_id;

    var popup = document.getElementById("popupFormPayment");
    popup.style.display = "block";

    fetch(`/load_invoice`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ inv_id: inv_id })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Response data:', data);  // Check the response data

        if (data.error) {
            console.error('Error:', data.error);
            return;
        }
        const dateString = data.due_date;
        const formattedDate = formatDate(dateString);

        document.getElementById("balanceText").value = data.balance || "";
        document.getElementById("currdueDate").value = formattedDate || "";
    })
    .catch(error => console.error('Fetch Error:', error));
}

// Close the popup form
document.getElementById("closeFormBtnPayment").onclick = function() {

    document.getElementById("payForm").reset();

    // Additionally clear any custom fields if needed
    document.getElementById("penaltyText").value = "0.00";
    document.getElementById("balanceText").value = "0";
    document.getElementById("updatedText").value = "0";
    
    document.getElementById("popupFormPayment").style.display = "none";
}

function setNextDueDate() {
    const paymentDate = document.getElementById('payDate').value;
    const nextDueDateInput = document.getElementById('nextdueDate');

    if (paymentDate) {
        const paymentDateObj = new Date(paymentDate);
        paymentDateObj.setDate(paymentDateObj.getDate() + 30);

        const year = paymentDateObj.getFullYear();
        const month = String(paymentDateObj.getMonth() + 1).padStart(2, '0');
        const day = String(paymentDateObj.getDate()).padStart(2, '0');

        nextDueDateInput.value = `${year}-${month}-${day}`;
    } else {
        nextDueDateInput.value = '';
    }
}

function updatePaymentMethodIcon(selectElement) {
    var selectedOption = selectElement.options[selectElement.selectedIndex];
    var iconUrl = selectedOption.getAttribute('data-icon-url');
    const otherPaymentMethodLabel = document.getElementById('other-payment-method-label');
    const otherPaymentMethodInput = document.getElementById('other-payment-method');

    if (selectElement.value === 'others') {
        otherPaymentMethodLabel.style.display = 'block';
        otherPaymentMethodInput.disabled = false;
    } else {
        otherPaymentMethodLabel.style.display = 'none';
        otherPaymentMethodInput.disabled = true;
        otherPaymentMethodInput.value = ''; // Clear the input value when hiding it
    }

    if (iconUrl) {
        selectElement.style.backgroundImage = 'url(' + iconUrl + ')';
        selectElement.style.backgroundSize = '70px';
        selectElement.style.backgroundRepeat = 'no-repeat';
        selectElement.style.backgroundPosition = 'right 10px center';
    } else {
        selectElement.style.backgroundImage = 'none'; // No icon for "Others"
    }
}

// Initialize icon on page load
document.addEventListener('DOMContentLoaded', function() {
    updatePaymentMethodIcon(document.getElementById('payment-method'));
});



function updatePenalty() {
    const dueDate = document.getElementById("currdueDate").value;
    const payDate = document.getElementById("payDate").value;
    
    if (dueDate && payDate) {
        const result = calculateOverdue(dueDate, payDate);
        document.getElementById("penaltyText").value = result.penaltyAmount;
        document.getElementById("updatedText").value = result.balanceAfterPenalty;
        document.getElementById("balanceText").value = parseFloat(document.getElementById("balanceText").value).toFixed(2);
    }
}

function calculateOverdue(currDueDate, payDate) {
    // Parse the dates
    const dueDate = new Date(currDueDate);
    const paymentDate = new Date(payDate);

    // Check if dates are valid
    if (isNaN(dueDate.getTime()) || isNaN(paymentDate.getTime())) {
        console.error('Invalid date');
        return { penaltyAmount: "0.00", balanceAfterPenalty: "0.00" };
    }

    // Calculate the difference in milliseconds
    const timeDiff = paymentDate - dueDate;
    
    // Convert milliseconds to days
    const daysOverdue = Math.ceil(timeDiff / (1000 * 60 * 60 * 24));
    
    // Calculate the penalty
    const penaltyRate = 0.05;
    const penaltyAmount = daysOverdue > 0 ? daysOverdue * penaltyRate : 0;
    
    // Assume balance is fetched and needs to be adjusted with penalty
    const initialBalance = parseFloat(document.getElementById("balanceText").value) || 0;
    const balanceAfterPenalty = (initialBalance + (initialBalance * penaltyAmount)).toFixed(2);
    
    return {
        penaltyAmount: (initialBalance * penaltyAmount).toFixed(2),
        balanceAfterPenalty: balanceAfterPenalty
    };
}

// Event listener for payment date changes to update penalty
document.getElementById("payDate").addEventListener("change", updatePenalty);

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('viewInvoiceBtn').addEventListener('click', function(event) {
        event.preventDefault(); // Prevent default form submission

        // Get values from the payment form
        let invoiceNumber = document.getElementById('invoiceNumber').value;
        const paymentDate = document.getElementById('payDate').value;
        const nextDueDate = document.getElementById('nextdueDate').value;
        const balance = document.getElementById('balanceText').value;
        const penalty = document.getElementById('penaltyText').value;
        const payment = document.getElementById('amountText').value;
        const updatedBalance = document.getElementById('updatedText').value;
    
        if (invoiceNumber.startsWith("INV #")) {
            invoiceNumber = invoiceNumber.replace("INV #", "").trim();
        }

        // Fetch the invoice data
        fetch(`/get_invoice_data?invoiceNumber=${invoiceNumber}`)
            .then(response => response.json())
            .then(data => {
                console.log('Data received:', data); // Log the data to inspect it

                if (data.error) {
                    console.error('Error fetching data:', data.error);
                } else {
                    // Populate the invoice table and other fields with the data received
                    populateInvoiceTable(data.invoice_data, data.inv_id, data.customer_data);

                    document.getElementById('invoicePaymentDate').textContent = paymentDate;
                    document.getElementById('invoiceNextDueDate').textContent = nextDueDate;
                    document.getElementById('invoiceBalance').textContent = balance;
                    document.getElementById('invoicePenalty').textContent = penalty;
                    document.getElementById('invoiceAmount').textContent = payment;
                    document.getElementById('invoiceUpdatedBalance').textContent = updatedBalance;

                    // Open the popup
                    document.getElementById('popupFormInvoice').style.display = 'block';
                }
            })
            .catch(error => console.error('Error:', error));
    });

    function populateInvoiceTable(invoiceData, invNum, customerData) {
        const tableBody = document.getElementById('popupInvoiceTableBody');
        tableBody.innerHTML = ''; // Clear existing rows

        invoiceData.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.code}</td>
                <td>${item.brand}</td>
                <td>${item.description}</td>
                <td>${item.quantity}</td>
                <td>${item.price}</td>
            `;
            tableBody.appendChild(row);
        });

        // Populate customer and invoice details
        document.getElementById('popup_invoice_id').textContent = invNum || "N/A";
        document.getElementById('popup_customer_name').textContent = customerData.cName || "N/A";
        document.getElementById('popup_customer_address').textContent = customerData.cAddress || "N/A";
        document.getElementById('popup_customer_email').textContent = customerData.cEmail || "N/A";
    }

    document.getElementById('closeFormBtnInvoice').addEventListener('click', function() {
        document.getElementById('popupFormInvoice').style.display = 'none';
    });
});