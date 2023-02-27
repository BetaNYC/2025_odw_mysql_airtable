SELECT org.org_post_id, Name, Email, Phone, airtable, post_title FROM 
	wp_gvxun9_posts AS posts 
	RIGHT JOIN 
		(SELECT post_id, CAST(meta_value as UNSIGNED) as org_post_id FROM wp_gvxun9_postmeta 
			WHERE meta_key = '_EventOrganizerID') as org
			ON posts.ID = org.post_id
		INNER JOIN (SELECT post_id, meta_value AS airtable FROM wp_gvxun9_postmeta WHERE meta_key = '_ecp_custom_41') AS meta
			ON org.post_id = meta.post_id
		LEFT JOIN (SELECT post_id , meta_value as Phone FROM wp_gvxun9_postmeta
					WHERE meta_key = '_OrganizerPhone') as org_phone
			ON org_phone.post_id  = org.org_post_id
		LEFT JOIN (SELECT post_id , meta_value as Email FROM wp_gvxun9_postmeta
				WHERE meta_key = '_OrganizerEmail') as org_email
			ON org_email.post_id  = org.org_post_id
		LEFT JOIN (select ID, post_title as Name FROM wp_gvxun9_posts WHERE post_type = 'tribe_organizer') as post_org
			ON post_org.ID = org.org_post_id
	WHERE post_type = 'tribe_events' AND post_status != 'trash'