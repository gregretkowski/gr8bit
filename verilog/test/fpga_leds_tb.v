module test();
    reg clk = 0;
    reg run = 1;
    reg zro = 0;
    reg [7:0] status;
    wire [5:0] led;

    fpga_leds u(
        clk,
        zro,
        run,
        status,
        led
    );

    always begin
        #1 clk = ~clk;
    end

    initial begin
        status[7:0] <= 8'b00000000;
        $display("Starting Test");
        $monitor("LED Value %b", led);
        #5 zro = 1'b1;
        #5 zro = 1'b0;
        #5 status = 8'hFF;
        #5 status = 8'h00;
        #100 ;
        #5 run = 1'b0;
        #5 ;
        $finish;
    end

    initial begin
        $dumpfile("fpga_leds.vcd");
        $dumpvars(0,test);
    end
endmodule