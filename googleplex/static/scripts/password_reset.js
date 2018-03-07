function submit_reset() {
  var valid = validate_reset();
  if (valid){
    document.getElementById('password-reset-form').submit(); //form submission
  }

  console.log('submit_registration returned ' + valid);

  return valid;
}
function validate_reset() {
  var err_count = 0;
  if (!validate_email()) err_count++;

  return err_count == 0;
}
function validate_email() {
  var email = document.getElementById('email');
  var email_error = document.getElementById('email-error');
  if (email.value.length == 0) {
    email_error.innerText = 'Email is required.';
    email_error.style.display = 'block';
    return false;
  } else {
    email_error.style.display = 'none';
    return true;
  }
}