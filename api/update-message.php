<?php
$req_admin = TRUE;
$get_json = TRUE;
require("access.php");
if (!isset($_GET['id'])) {
	die_error(400, "Should have id!");
}
$target_id = intval($_GET['id']);
if (!is_array($json_data) || !isset($json_data['title']) || !isset($json_data['data'])) {
	die_error(400, "Bad JSON - must be an object with title and data.");
}
$new_title = $json_data['title'];
$new_data = $json_data['data'];
if (!is_string($new_title) || !is_string($new_data)) {
	die_error(400, "Bad JSON - Subtype mismatch.");
}
$qry = $db->prepare("UPDATE `Posts` SET `Title` = ? , `Contents` = ? WHERE `UID` = ?");
if ($qry === FALSE || !$qry->bind_param("ssi", $new_title, $new_data, $target_id) || !$qry->execute() || !$qry->close()) {
	die_error(500, "Server Error: Could not submit body query.");
}
echo json_encode(array());
