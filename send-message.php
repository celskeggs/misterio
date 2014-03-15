<?php
$req_admin = FALSE;
$get_json = TRUE;
require("access.php");
set_json();
if (!is_array($json_data) || !isset($json_data['public']) || !isset($json_data['title']) || !isset($json_data['data']) || !isset($json_data['to'])) {
	die_error(400, "Bad JSON - must be an object with public, title, data, and to.");
}
$post_is_public = $json_data['public'] ? 1 : 0;
$post_data = utf8_decode($json_data['data']);
$post_title = utf8_decode($json_data['title']);
$post_prev = isset($json_data['prev']) ? $json_data['prev'] : NULL;
$post_recipients = $json_data['to'];
if (!is_string($post_data) || !is_string($post_title) || !is_array($post_recipients) || ($post_prev != NULL && !is_int($post_prev))) {
	die_error(400, "Bad JSON - Subtype mismatch.");
}
foreach ($post_recipients as $value) {
	if (!is_int($value)) {
		die_error(400, "Bad JSON - Recipient type mismatch.");
	}
}
$post_date_timestamp = time();
$post_date = date('Y-m-d H:i:s', $post_date_timestamp);
// author, ispublic, data, title, prev
$qry = $db->prepare("INSERT INTO `Posts` (`Author`, `IsPublic`, `Date`, `Contents`, `Title`, `ResponseTo`, `Instance`) VALUES (?, ?, ?, ?, ?, ?, ?)");
if ($qry === FALSE || !$qry->bind_param("iisssii", $user_uid, $post_is_public, $post_date, $post_data, $post_title, $post_prev, $user_instance) || !$qry->execute() || !$qry->close()) {
	die_error(500, "Server Error: Could not submit body query.");
}
$post_id = $db->insert_id;
if (!is_int($post_id) || $post_id <= 0) {
	die_error(500, "Server Error: Index assertion failed.");
}
if (count($post_recipients) > 0) {
	$qry = $db->prepare("INSERT INTO `PostRecipients` (`PostID`,`RecipientID`) VALUES (?, ?)");
	$post_recipient_id_single = 0;
	if ($qry === FALSE || !$qry->bind_param("ii", $post_id, $post_recipient_id_single)) {
		die_error(500, "Server Error: Could not prepare recipient query.");
	}
	foreach ($post_recipients as $value) {
		$post_recipient_id_single = $value;
		if (!$qry->execute()) {
			die_error(500, "Server Error: Could not commit recipients.");
		}
	}
	if (!$qry->close()) {
		die_error(500, "Server Error: Could not finish recipients.");
	}
}
echo json_encode(array('id' => $post_id, 'date' => $post_date_timestamp * 1000));
