<?php
$req_admin = TRUE;
$get_json = TRUE;
require("access.php");
set_json();
if (!is_array($json_data) || !isset($json_data['name']) || !isset($json_data['email']) || !isset($json_data['access']) || !isset($json_data['avatar'])) {
	die_error(400, "Bad JSON - must be an object with name, email, access, and avatar.");
}
$new_access = $json_data['access'] ? 1 : 0;
$new_avatar = $json_data['avatar'];
$new_name = $json_data['name'];
$new_email = $json_data['email'] !== null ? $json_data['email'] : "";
if (!is_string($new_name) || !is_string($new_avatar) || !is_string($new_email)) {
	die_error(400, "Bad JSON - Subtype mismatch.");
}
if ($new_email === "") {
	$new_email = null;
	$new_token = null;
} else {
	$new_token = generate_token();
}
$qry = $db->prepare("INSERT INTO `Players` (`Name`, `Token`, `Email`, `Admin`, `Avatar`) VALUES (?, ?, ?, ?, ?)");
if ($qry === FALSE || !$qry->bind_param("sssis", $new_name, $new_token, $new_email, $new_access, $new_avatar) || !$qry->execute() || !$qry->close()) {
	die_error(500, "Server Error: Could not submit body query.");
}
$new_id = $db->insert_id;
if (!is_int($new_id) || $new_id <= 0) {
	die_error(500, "Server Error: Index assertion failed.");
}
if ($new_email !== null) {
	mail($new_email, "Tienes una cuenta del Misterio en Cuzco!", "Hola!\nAhora, tú tienes una cuenta del Misterio en Cuzco.\nPuedes entrar con este enlace: " . $config_base_url . $new_token . "\n");
}
echo json_encode(array('uid' => $new_id));
