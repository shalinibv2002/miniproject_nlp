"""Step 6 conservative final-dataset promotion tests."""

from backend.database.init_db import get_connection, init_db
from backend.database.candidate_promotion import promote_candidates
from backend.database.seed_reference_data import seed


def test_good_candidates_promote_and_exact_date_duplicates_merge(tmp_path, monkeypatch):
    path=str(tmp_path/'promote.db'); init_db(path); seed(db_path=path)
    import backend.database.candidate_promotion as module
    monkeypatch.setattr(module,'init_db',lambda:None)
    c=get_connection(path)
    try:
        c.execute("INSERT INTO collection_runs (status) VALUES ('completed')"); cr=c.execute('select last_insert_rowid()').fetchone()[0]
        c.execute("INSERT INTO extraction_runs (collection_run_id,status) VALUES (?, 'completed')",(cr,)); er=c.execute('select last_insert_rowid()').fetchone()[0]
        c.execute("INSERT INTO raw_source_occurrences (collection_run_id,source_url,normalized_url,source_type) VALUES (?,?,?,'html')",(cr,'https://www.tce.edu/a','https://www.tce.edu/a')); src=c.execute('select last_insert_rowid()').fetchone()[0]
        for title,date,status in [('NCC Workshop','2024-08-15','GOOD'),('NCC Workshop','2024-08-15','GOOD'),('NCC Workshop','2025-08-15','GOOD'),('Policy','2024-08-15','NON_ACTIVITY'),('Aggregate','2024-08-15','REVIEW')]:
            c.execute("INSERT INTO activity_candidates (extraction_run_id,source_occurrence_id,title,description,activity_date,academic_year,department,evidence_text,extraction_method,extraction_confidence) VALUES (?,?,?,?,?,?,?,?,?,?)",(er,src,title,title,date,'2024-25','[\"GENERAL\"]',title,'test',.8)); cid=c.execute('select last_insert_rowid()').fetchone()[0]
            c.execute("INSERT INTO candidate_quality_reviews (candidate_id,quality_status) VALUES (?,?)",(cid,status))
            if status=='GOOD': c.execute("INSERT INTO candidate_classifications (candidate_id,final_category,classification_confidence,hint_match_status) VALUES (?,'NCC',.8,'NO_HINT')",(cid,))
        c.execute("INSERT INTO institutional_activities (title,normalized_title) VALUES ('Existing','existing')"); c.commit()
        report=promote_candidates(c,er)
        assert report['final_activities']==2 and report['merged_duplicates']==1
        assert c.execute('select count(*) from institutional_activities').fetchone()[0]==3
        assert c.execute('select count(*) from activity_categories').fetchone()[0]==2
        assert c.execute('select count(*) from activity_candidate_links').fetchone()[0]==3
        assert c.execute("select count(*) from activity_candidates where title in ('Policy','Aggregate')").fetchone()[0]==2
    finally: c.close()
