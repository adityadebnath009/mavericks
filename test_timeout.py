try:
    raise TimeoutError("INCOIS OPENDAP remote server timed out.")
except Exception as e:
    err_msg = str(e)
    print("err_msg:", err_msg)
    print("timeout in err_msg?", "timeout" in err_msg.lower())
    if "timeout" in err_msg.lower():
        print("Caught it!")
    else:
        print("Hit else branch")
