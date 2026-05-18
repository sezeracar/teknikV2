streamlit.errors.StreamlitDuplicateElementId: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).

Traceback:
File "/mount/src/teknikv2/v3.py", line 171, in <module>
    if kullanici_giris_kontrol():
       ~~~~~~~~~~~~~~~~~~~~~~~^^
File "/mount/src/teknikv2/v3.py", line 118, in kullanici_giris_kontrol
    if st.button(f"🚪 Çıkış Yap ({st.session_state.aktif_kullanici.capitalize()})"):
       ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/runtime/metrics_util.py", line 698, in wrapped_func
    result = non_optional_func(*args, **kwargs)
File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/elements/widgets/button.py", line 379, in button
    return self.dg._button(
           ~~~~~~~~~~~~~~~^
        label,
        ^^^^^^
    ...<12 lines>...
        shortcut=shortcut,
        ^^^^^^^^^^^^^^^^^^
    )
    ^
File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/elements/widgets/button.py", line 1642, in _button
    element_id = compute_and_register_element_id(
        "form_submit_button" if is_form_submitter else "button",
    ...<10 lines>...
        shortcut=normalized_shortcut,
    )
File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/elements/lib/utils.py", line 264, in compute_and_register_element_id
    _register_element_id(ctx, element_type, element_id)
    ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/elements/lib/utils.py", line 149, in _register_element_id
    raise StreamlitDuplicateElementId(element_type)
