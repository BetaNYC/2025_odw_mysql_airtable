SELECT name_t.post_id , Name, Email , airtable_id ,survey FROM 
	(SELECT post_id, meta_value as Name FROM wp_gvxun9_postmeta
		WHERE meta_key = "_tribe_rsvp_full_name") as name_t
	LEFT JOIN (SELECT post_id, meta_value as Email FROM wp_gvxun9_postmeta
		WHERE meta_key = "_tribe_rsvp_email") as email_t
		on name_t.post_id = email_t.post_id 
	LEFT JOIN (SELECT post_id, CAST(meta_value AS UNSIGNED) AS event_id FROM wp_gvxun9_postmeta
		WHERE meta_key = "_tribe_rsvp_event") as event_lookup_t
		on name_t.post_id = event_lookup_t.post_id 
	LEFT JOIN (SELECT post_id, meta_value AS airtable_id
		FROM wp_gvxun9_postmeta 
		WHERE meta_key = "_ecp_custom_41" AND meta_value NOT IN ("","None")) AS meta_airtable
		on meta_airtable.post_id = event_lookup_t.event_id 
	LEFT JOIN (SELECT post_id, meta_value AS survey FROM wp_gvxun9_postmeta
		WHERE meta_key = "_tribe_tickets_meta") as survey_t
		on name_t.post_id = survey_t.post_id 