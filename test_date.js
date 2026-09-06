const d = new Date();
const pad = (n) => n.toString().padStart(2, '0');
const localString = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
console.log(localString);
