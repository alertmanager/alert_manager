import sys
import json
import urllib2


def normalize_bool(value):
    return True if value.lower() in ('1', 'true') else False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        payload = json.loads(sys.stdin.read())
        print >> sys.stderr, "INFO Alert Manager called. payload: %s" % json.dumps(payload)
    else:
        print >> sys.stderr, "FATAL Unsupported execution mode (expected --execute flag)"
        sys.exit(1)
