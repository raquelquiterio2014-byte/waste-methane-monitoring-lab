import pytest
from storage import save_review,list_reviews

def test_save_and_read(tmp_path):
    db=tmp_path/'nested'/'reviews.sqlite3'
    save_review('abc','needs_evidence','Needs source verification',{'x':1},db)
    rows=list_reviews(db)
    assert len(rows)==1 and rows[0]['reviewer_note']=='Needs source verification'

def test_reject_empty_note(tmp_path):
    with pytest.raises(ValueError): save_review('abc','approved',' ',{},tmp_path/'test.sqlite3')
